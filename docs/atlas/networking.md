---
type: concept
title: Networking and Traffic Management
summary: Ingress routing, public IPv4 Cloud SQL connectivity with mTLS, and cross-origin resource sharing.
related: ["architecture.md", "compute.md", "database.md", "storage.md"]
source_paths: ["modules/cloudrun/main.tf", "modules/cloudsql/main.tf", "modules/storage/main.tf"]
---

# Networking and Traffic Management

The networking configuration of `sample-infra` balances simplicity, serverless scalability, and strong encryption. It governs external ingress, communication between Cloud Run and Cloud SQL, and cross-origin resource sharing for storage assets.

## External Ingress & Edge Routing

All external client traffic reaches the application stack through Google's global edge network:

```
+--------------------------------------------------------------------------------+
|                             Google Edge Network                                |
|  - Managed TLS Termination (HTTPS)                                             |
|  - Ingress Policy: INGRESS_TRAFFIC_ALL                                         |
+---------------------------------------+----------------------------------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
+---------------------------------+           +----------------------------------+
| Frontend Ingress (Cloud Run)    |           | Backend Ingress (Cloud Run)      |
| - Port: 8080                    |           | - Port: 8000                     |
| - roles/run.invoker to allUsers |           | - roles/run.invoker to allUsers  |
| - Output: frontend_url          |           | - Output: backend_url            |
+---------------------------------+           +----------------------------------+
```

### Ingress Features
- **Traffic Mode:** Both `frontend` and `backend` services set `ingress = "INGRESS_TRAFFIC_ALL"`.
- **Port Mapping:** The frontend container exposes port `8080` (standard for unprivileged Nginx) and the backend container exposes port `8000` (FastAPI standard).
- **Public Authorization:** Public invoker IAM policy bindings (`roles/run.invoker` for `allUsers`) permit unauthenticated edge traffic to reach both services.
- **Automated TLS:** HTTPS certificates and TLS handshakes are managed automatically by Google Cloud infrastructure.

## Cloud SQL Connectivity Architecture

Unlike traditional VPC-peered deployments that require a Serverless VPC Access connector, this architecture utilizes direct, secure connectivity to Google Cloud SQL:

```
+-------------------------------------------------------+
| Cloud Run Service / Job                               |
| (sample-backend or sample-migration)                  |
|                                                       |
|  +-------------------------------------------------+  |
|  | Cloud SQL Python Connector (Async Driver)       |  |
|  +------------------------+------------------------+  |
+---------------------------|---------------------------+
                            |
                            | Ephemeral mTLS Tunnel
                            | Port 5432 over Public IPv4
                            v
+-------------------------------------------------------+
| Google Cloud SQL PostgreSQL Instance                  |
| - ipv4_enabled = true                                 |
| - cloudsql.iam_authentication = "on"                  |
| - Authorized Networks: Optional CIDR blocks           |
+-------------------------------------------------------+
```

### Design Advantages
- **No VPC Connector Overhead:** Eliminates the latency, throughput bottlenecks, and ongoing idle compute costs associated with Serverless VPC Access connectors.
- **End-to-End Mutual TLS:** The Cloud SQL Python Connector establishes an ephemeral mutual TLS (mTLS) tunnel directly with the Cloud SQL instance, securing all in-flight traffic.
- **IAM Authorization:** The connection is authenticated at the database engine level via Google Cloud IAM, requiring no static passwords.
- **Authorized Networks:** Administrators can optionally specify a list of authorized IPv4 CIDR blocks (`var.authorized_networks`) for maintenance or direct access.

## Cross-Origin Resource Sharing (CORS)

Cross-origin policies are defined at both the backend service and the asset bucket:
- **Storage Bucket CORS:** The `modules/storage` module configures origin allowances for `https://*.run.app`, custom application domains, and local development (`http://localhost:5173`), permitting `GET`, `PUT`, and `OPTIONS` operations with a 3600-second preflight cache.
- **Direct Upload Handshake:** Browsers request pre-signed upload URLs from the backend API, perform CORS preflight options requests against Google Cloud Storage, and upload payloads directly to the storage bucket.
