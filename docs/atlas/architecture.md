---
type: concept
title: Cloud Infrastructure Architecture
summary: Architectural blueprint and module integration connecting frontend, backend, relational database, object storage, and secrets management.
related: ["overview.md", "compute.md", "database.md", "storage.md", "security.md", "networking.md", "deployment.md"]
source_paths: ["environments/dev/main.tf", "environments/dev/outputs.tf", "environments/dev/variables.tf", "environments/dev/versions.tf"]
---

# Cloud Infrastructure Architecture

The infrastructure architecture for the sample application stack is built on a serverless, managed-services foundation hosted on Google Cloud Platform. It minimizes operational overhead by leveraging fully managed compute, database, and storage platforms while enforcing strict isolation, least-privilege IAM bindings, passwordless database connectivity, and automated secrets management.

## Architectural Layers

```
+--------------------------------------------------------------------------------+
|                                1. Ingress Tier                                 |
|         - HTTPS / TLS Termination (Google Edge Infrastructure)                 |
|         - Cloud Run Ingress: INGRESS_TRAFFIC_ALL                               |
|         - Public Invoker IAM: roles/run.invoker to allUsers                    |
+--------------------------------------------------------------------------------+
          |                                                   |
          | HTTP Requests                                     | Pre-signed PUT / GET
          v                                                   v
+----------------------------------+          +----------------------------------+
|      2. Presentation Tier        |          |      4. Object Storage Tier      |
|  - Cloud Run: sample-frontend    |          |  - Google Cloud Storage Bucket   |
|  - Port 8080 (Nginx unprivileged)|          |  - UBLA: true, PAP: enforced     |
|  - SPA Static Routing & Gzip     |          |  - CORS for Direct Browser Upload|
+----------------------------------+          +----------------------------------+
          |                                                   ^
          | REST API Calls (JSON)                             |
          v                                                   | Issues V4
+----------------------------------+                          | Signed URLs
|     3. Application API Tier      |                          |
|  - Cloud Run: sample-backend     +--------------------------+
|  - FastAPI (Port 8000)           |
|  - DB Env: DATABASE_INSTANCE,    |
|    DB_USER, DB_NAME, PROJECT_ID  |
+-----------------+----------------+
                  |
        Cloud SQL | Cloud SQL Connector
        IAM Auth  | mTLS over Public IPv4
                  v
+----------------------------------+          +----------------------------------+
|    5. Relational Database Tier   |          |      6. Secrets & Config Tier    |
|  - Cloud SQL PostgreSQL 16       |          |  - Google Cloud Secret Manager   |
|  - SSD Storage (PD_SSD)          |<---------+  - JWT_SECRET (32-char random)   |
|  - disk_autoresize = true        |          |  - DATABASE_INSTANCE (Conn Name) |
|  - IAM DB Users (CLOUD_IAM_...)  |          |                                  |
+-----------------+----------------+          +----------------------------------+
                  ^
                  | Runs "alembic upgrade head"
+-----------------+----------------+
|      7. Migration Job Tier       |
|  - Cloud Run Job: migration      |
|  - Identity: sa-migrator         |
+----------------------------------+
```

### 1. Ingress Tier
External client traffic arrives over HTTPS. Both backend and frontend services are configured with `ingress = "INGRESS_TRAFFIC_ALL"` in [Compute](compute.md) and bind `roles/run.invoker` to `allUsers`. Google Cloud Run handles TLS termination and traffic routing automatically.

### 2. Presentation Tier
The frontend is deployed as a serverless container running unprivileged Nginx on port `8080`. It serves pre-compiled single-page application assets and routes API requests to the backend service.

### 3. Application API Tier
The backend runs containerized FastAPI on port `8000` via [Compute](compute.md). It receives connection details (`DATABASE_INSTANCE`, `DB_USER`, `DB_NAME`, `GCS_BUCKET_NAME`) via environment variables and uses the Cloud SQL Python Connector with IAM database authentication to interact with Cloud SQL.

### 4. Object Storage Tier
File uploads and static assets bypass application compute pipes and stream directly into [Object Storage](storage.md):
- Bucket provisioned with Uniform Bucket-Level Access (UBLA) and Public Access Prevention set to `enforced`.
- CORS configured for browser uploads (`GET`, `PUT`, `OPTIONS` methods, allowed headers, max age 3600 seconds).
- Backend service account is granted `roles/storage.objectAdmin` to generate V4 pre-signed upload and download URLs.

### 5. Relational Database Tier
Structured data persists in a managed [Database](database.md):
- Cloud SQL running PostgreSQL 16 on SSD persistent storage (`PD_SSD`) with auto-resizing enabled.
- Database access is strictly passwordless: `cloudsql.iam_authentication` flag is enabled, and IAM database users (`backend` and `migrator`) are provisioned using `CLOUD_IAM_SERVICE_ACCOUNT` identities.
- Connectivity uses public IPv4 with optional authorized networks and end-to-end mTLS through Cloud SQL Connector.

### 6. Secrets & Identity Tier
Security boundaries are enforced via [Security](security.md):
- Dedicated service accounts (`sa-backend`, `sa-frontend`, `sa-migrator`) with minimal necessary role bindings.
- Google Cloud Secret Manager provisions `JWT_SECRET` (auto-generated 32-character cryptographic string) and `DATABASE_INSTANCE` (Cloud SQL instance connection name string).

### 7. Migration Job Tier
Database schema updates are isolated from normal application runtime instances:
- Defined as a Google Cloud Run v2 Job executing `["alembic", "upgrade", "head"]`.
- Executes under the dedicated identity `sa-migrator` with IAM database user authentication.
- Can be invoked prior to revision promotion via the `migration_job_execute_command` output.
