---
type: concept
title: IAM, Secrets, and Security Architecture
summary: Principle of least privilege, service account roles, Secret Manager secrets injection, and security boundary enforcement.
related: ["architecture.md", "database.md", "storage.md", "compute.md"]
source_paths: []
---

# IAM, Secrets, and Security Architecture

The security architecture of `sample-infra` implements defense-in-depth across identity, network, data, and secret boundaries. It strictly adheres to the principle of least privilege, eliminates hardcoded credentials, and automates secret provisioning through managed GCP services.

## Identity & Access Management (IAM)

Each workload runs under a dedicated Google Service Account (GSA) with bounded, resource-level role bindings:

```
+-----------------------------------------------------------------------------------------+
|                                    Workload Identities                                  |
+-----------------------------------------------------------------------------------------+
| Backend Service Account           | Cloud SQL Client (`roles/cloudsql.client`)          |
| (sa-backend@proj.iam.gservice)    | Cloud SQL Instance User (`roles/cloudsql.instanceUser`)|
|                                   | Storage Object Admin (`roles/storage.objectAdmin`)  |
|                                   | Secret Manager Accessor (`roles/secretmanager.secretAccessor`)|
+-----------------------------------+-----------------------------------------------------+
| Frontend Service Account          | Minimal Base Execution (`roles/run.invoker`)         |
| (sa-frontend@proj.iam.gservice)   | No access to Database, Storage, or Secrets          |
+-----------------------------------+-----------------------------------------------------+
| Migration Job Service Account     | Cloud SQL Client (`roles/cloudsql.client`)          |
| (sa-migrator@proj.iam.gservice)   | Cloud SQL Admin (`roles/cloudsql.admin` / DB owner) |
|                                   | Secret Manager Accessor                             |
+-----------------------------------+-----------------------------------------------------+
| Deployment CI/CD Account          | Cloud Run Developer (`roles/run.developer`)         |
| (sa-deployer@proj.iam.gservice)   | Artifact Registry Writer (`roles/artifactregistry.writer`)|
|                                   | Service Account User (`roles/iam.serviceAccountUser`)|
+-----------------------------------------------------------------------------------------+
```

### Granular Resource Boundaries
- Service accounts are not granted project-wide permissions. Storage roles are bound directly to the application bucket (`gs://<PROJECT_ID>-assets`).
- Secret Manager accessor permissions are scoped to specific secret resource IDs rather than all secrets in the project.

## Secret Management

Application secrets are managed centrally through **Google Cloud Secret Manager**. This prevents credentials from entering source control, build artifacts, or plain-text environment variables.

```
+----------------------------------+
|   Google Cloud Secret Manager    |
|                                  |
|   - JWT_SECRET                   |
|   - SMTP_HOST / SMTP_PORT        |
|   - SMTP_USER / SMTP_PASSWORD    |
|   - DATABASE_URL (Fallback)      |
+-----------------+----------------+
                  |
                  | Secret Manager API
                  | (Fetch on Startup)
                  v
+----------------------------------+
|      FastAPI Backend Process     |
|      (app/core/config.py)        |
+----------------------------------+
```

### Secret Resolution Order
The backend uses a cascading resolution workflow:
1. **Local Environment:** Checks for OS environment variables (ideal for local development and unit tests).
2. **Secret Manager Fallback:** If an environment variable is omitted and the application runs in GCP, the `google-cloud-secret-manager` client fetches the latest active secret version using the container's service account identity.

## Network & Application Security Controls

1. **Transport Encryption:**
   - All inbound traffic to Cloud Run services is forced to HTTPS over TLS 1.2/1.3 with Google-managed certificates.
   - Internal traffic between Cloud Run and Cloud SQL is encrypted via mutual TLS tunnels managed by the Cloud SQL Connector.

2. **Frontend Security Headers:**
   Nginx is configured to inject mandatory HTTP response security headers:
   - `Content-Security-Policy (CSP)`: Restricts script, style, and media sources to trusted origins.
   - `Strict-Transport-Security (HSTS)`: Forces browsers to use HTTPS for future interactions (`max-age=31536000; includeSubDomains`).
   - `X-Content-Type-Options: nosniff`: Prevents MIME-sniffing exploits.
   - `X-Frame-Options: SAMEORIGIN`: Protects against clickjacking.
