---
type: concept
title: IAM, Secrets, and Security Architecture
summary: Least-privilege IAM service accounts, passwordless database authentication, and Secret Manager integration.
related: ["architecture.md", "compute.md", "database.md", "storage.md"]
source_paths: ["modules/iam/main.tf", "modules/iam/variables.tf", "modules/iam/outputs.tf", "modules/iam/tests/iam_validation.tftest.hcl", "tests/test_iam_module.py"]
---

# IAM, Secrets, and Security Architecture

The security architecture of `sample-infra` implements defense-in-depth across identity, database authentication, storage authorization, and secret injection. It strictly follows the principle of least privilege, eliminating long-lived credentials and enforcing declarative role bindings.

## Workload Service Accounts & Role Bindings

The `modules/iam` module establishes dedicated Google Service Accounts (GSAs) and project-level IAM role memberships for each distinct system workload:

```
+-----------------------------------------------------------------------------------------+
|                                    Workload Identities                                  |
+-----------------------------------------------------------------------------------------+
| Backend Service Account           | Cloud SQL Client (`roles/cloudsql.client`)          |
| (sa-backend)                      | Cloud SQL Instance User (`roles/cloudsql.instanceUser`)|
|                                   | Secret Manager Accessor (`roles/secretmanager.secretAccessor`)|
|                                   | Storage Object Admin (`roles/storage.objectAdmin`)  |
+-----------------------------------+-----------------------------------------------------+
| Migration Job Service Account     | Cloud SQL Client (`roles/cloudsql.client`)          |
| (sa-migrator)                     | Cloud SQL Instance User (`roles/cloudsql.instanceUser`)|
|                                   | Secret Manager Accessor (`roles/secretmanager.secretAccessor`)|
+-----------------------------------+-----------------------------------------------------+
| Frontend Service Account          | Cloud Run Invoker (`roles/run.invoker`)             |
| (sa-frontend)                     | (No access to Database, Secrets, or Object Storage) |
+-----------------------------------------------------------------------------------------+
```

### Least Privilege Boundaries
- **sa-backend:** Granted access to query Cloud SQL via IAM DB auth, retrieve secrets from Secret Manager, and generate V4 pre-signed URLs or mutate objects in the storage bucket.
- **sa-migrator:** Granted minimal rights needed to execute database schema updates (`roles/cloudsql.client`, `roles/cloudsql.instanceUser`, and `roles/secretmanager.secretAccessor`). It does not hold project administrative rights or storage permissions.
- **sa-frontend:** Restricted to basic execution privileges (`roles/run.invoker`). It cannot query the database, access secret payloads, or touch object storage.

## Secret Management

Sensitive runtime parameters are provisioned in Google Cloud Secret Manager (configured in `environments/dev/main.tf`):

```
+-----------------------------------------+
|       Google Cloud Secret Manager       |
+-----------------------------------------+
| 1. JWT_SECRET                           |
|    - 32-character cryptographic string  |
|    - Generated via random_password      |
|    - Stored in automatic replication    |
+-----------------------------------------+
| 2. DATABASE_INSTANCE                    |
|    - Cloud SQL connection identifier    |
|    - Sourced from module.cloudsql       |
+-----------------------------------------+
```

Workloads retrieve these secrets during startup or bootstrap lifespan via the `secretmanager.secretAccessor` role.

## Zero Static Passwords Policy

Across the entire infrastructure codebase:
- Relational database connections do not use static passwords or database credentials.
- Cloud SQL enables IAM authentication (`cloudsql.iam_authentication = "on"`).
- Both `sa-backend` and `sa-migrator` authenticate to PostgreSQL using short-lived OAuth tokens issued through the Cloud SQL Admin API and Cloud SQL Python Connector.
- Tests continuously assert that no `password` or `root_password` attributes exist in modules or environment definitions.

## Public Invoker Boundaries

Public internet access to the frontend web application and backend API is controlled via Cloud Run IAM members:
- `google_cloud_run_v2_service_iam_member.backend_invoker` binds `roles/run.invoker` to `allUsers`.
- `google_cloud_run_v2_service_iam_member.frontend_invoker` binds `roles/run.invoker` to `allUsers`.
- Deployed services run in isolated sandboxed microVMs managed by Cloud Run.

## Module Inputs & Outputs

### Input Variables
- `project_id` (string, required): The target GCP project identifier.

### Module Outputs
- `backend_sa_email`: Email address for `sa-backend`.
- `backend_sa_id`: Fully qualified ID for `sa-backend`.
- `backend_sa_unique_id`: Unique numerical ID for `sa-backend`.
- `frontend_sa_email`: Email address for `sa-frontend`.
- `frontend_sa_id`: Fully qualified ID for `sa-frontend`.
- `frontend_sa_unique_id`: Unique numerical ID for `sa-frontend`.
- `migrator_sa_email`: Email address for `sa-migrator`.
- `migrator_sa_id`: Fully qualified ID for `sa-migrator`.
- `migrator_sa_unique_id`: Unique numerical ID for `sa-migrator`.

## Validation & Testing

- **OpenTofu Test Suite** (`modules/iam/tests/iam_validation.tftest.hcl`): Verifies that service account outputs are non-empty during mock plan evaluation.
- **Python Integration Tests** (`tests/test_iam_module.py`): Verifies `project_id` is required without default, confirms service account names and least-privilege role mappings, and validates module syntax with OpenTofu.
