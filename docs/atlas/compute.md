---
type: concept
title: Container Runtimes and Compute Services
summary: Serverless Cloud Run v2 services and database migration jobs provisioned via OpenTofu.
related: ["architecture.md", "networking.md", "security.md", "database.md", "deployment.md"]
source_paths: ["modules/cloudrun/main.tf", "modules/cloudrun/variables.tf", "modules/cloudrun/outputs.tf", "modules/cloudrun/tests/cloudrun_validation.tftest.hcl", "tests/test_cloudrun_module.py"]
---

# Container Runtimes and Compute Services

The compute tier is encapsulated in `modules/cloudrun`. It provisions serverless container workloads using Google Cloud Run v2 resources, managing the lifecycle of web-facing services and isolated batch jobs.

## Module Resources

The module declares three primary GCP resources:

1. `google_cloud_run_v2_service.backend`: Asynchronous FastAPI REST API service.
2. `google_cloud_run_v2_service.frontend`: Single-page application static web server.
3. `google_cloud_run_v2_job.migration`: Batch job executing Alembic database migrations.

Additionally, public HTTP access is granted by attaching `google_cloud_run_v2_service_iam_member` resources binding role `roles/run.invoker` to `allUsers` for both frontend and backend services.

## Service Specifications

| Parameter | Frontend Service (`sample-frontend`) | Backend Service (`sample-backend`) | Migration Job (`sample-migration`) |
| :--- | :--- | :--- | :--- |
| **Resource Type** | `google_cloud_run_v2_service` | `google_cloud_run_v2_service` | `google_cloud_run_v2_job` |
| **Listening Port** | `8080` | `8000` | N/A (Batch process) |
| **Service Account** | `var.frontend_sa_email` | `var.backend_sa_email` | `var.migrator_sa_email` |
| **Ingress Mode** | `INGRESS_TRAFFIC_ALL` | `INGRESS_TRAFFIC_ALL` | N/A |
| **Scaling Limits** | `min_instance_count`: 0, `max_instance_count`: 10 | `min_instance_count`: 0, `max_instance_count`: 10 | Executes on demand |
| **Entrypoint Command** | Default container entrypoint | Default container entrypoint | `["alembic", "upgrade", "head"]` |

## Environment Variables Configuration

### Backend Service Environment
The backend service automatically receives database connection details and project metadata:
- `DATABASE_INSTANCE`: Cloud SQL instance connection name (format: `project:region:instance`).
- `DB_USER`: IAM database username, formatted by trimming `.gserviceaccount.com` from `backend_sa_email`.
- `DB_NAME`: Target database name (e.g. `postgres` or `sampledb`).
- `GCP_PROJECT_ID`: Target GCP project identifier.
- Dynamic key-value pairs passed via `var.backend_env_vars` (such as `GCS_BUCKET_NAME`).

### Migration Job Environment
The migration job receives the same database targeting variables:
- `DATABASE_INSTANCE`: Cloud SQL instance connection name.
- `DB_USER`: IAM database username, trimmed from `migrator_sa_email`.
- `DB_NAME`: Target database name.
- Dynamic environment variables passed via `var.migration_env_vars`.

## Module Inputs & Outputs

### Key Input Variables
- `project_id` (string, required): The GCP project ID where Cloud Run resources are provisioned.
- `region` (string, required): The GCP region for the Cloud Run resources.
- `backend_image` (string, required): Container image URL for the backend service.
- `frontend_image` (string, required): Container image URL for the frontend service.
- `migrator_image` (string, optional): Container image URL for the migration job (defaults to `backend_image`).
- `backend_sa_email`, `frontend_sa_email`, `migrator_sa_email` (string, required): Service account emails.
- `database_instance` / `database_instance_connection_name` (string, optional): Cloud SQL connection name.
- `database_name` (string, optional, default: `"postgres"`): PostgreSQL database name.
- `min_instance_count` (number, default: 0) and `max_instance_count` (number, default: 10): Service instance limits.
- `deletion_protection` (bool, default: `false`): Deletion protection toggle.

### Module Outputs
- `backend_url`: Public HTTPS URL of the backend service (`google_cloud_run_v2_service.backend.uri`).
- `frontend_url`: Public HTTPS URL of the frontend service (`google_cloud_run_v2_service.frontend.uri`).
- `migration_job_name`: Identifier of the migration job (`google_cloud_run_v2_job.migration.name`).
- `backend_service_name`, `frontend_service_name`: Resource names for the services.
- `backend_service_id`, `frontend_service_id`, `migration_job_id`: Fully qualified resource identifiers.

## Validation & Testing

The module's correctness is validated through two complementary test layers:
- **OpenTofu Test Suite** (`modules/cloudrun/tests/cloudrun_validation.tftest.hcl`): Mocks the Google provider and validates scaling parameters, port assignments (8000 for backend, 8080 for frontend), public invoker bindings, and migration job entrypoint commands during speculative plan execution.
- **Python Integration Tests** (`tests/test_cloudrun_module.py`): Verifies required variable declarations without default values, resource definitions, environment variable propagation, and executes `tofu fmt` and `tofu validate`.
