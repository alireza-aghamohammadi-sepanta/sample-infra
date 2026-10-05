---
type: concept
title: CI/CD and Deployment Workflows
summary: Declarative OpenTofu environment orchestration, API provisioning, migration job execution, and test validation.
related: ["overview.md", "architecture.md", "compute.md", "database.md"]
source_paths: [".gitignore", "environments/dev/backend.tf.example", "environments/dev/main.tf", "environments/dev/outputs.tf", "environments/dev/terraform.tfvars.example", "environments/dev/variables.tf", "environments/dev/versions.tf", "tests/test_dev_environment.py"]
---

# CI/CD and Deployment Workflows

Infrastructure deployment in `sample-infra` is managed declaratively using OpenTofu / Terraform. The configuration ties together modular infrastructure components into complete environment instances, coordinates API enablement, manages secrets, and provides execution hooks for database migrations.

## Environment Orchestration (`environments/dev`)

The development environment definition lives in `environments/dev` and serves as the deployment blueprint:

```
environments/dev/
├── versions.tf              # Provider & OpenTofu version constraints
├── variables.tf             # Input variables (project_id, images, tier, bucket)
├── main.tf                  # API activation, module wiring, and secrets
├── outputs.tf               # Exported endpoints, identifiers, and CLI commands
├── backend.tf.example       # Template for migrating to remote GCS state
└── terraform.tfvars.example # Template for local environment variable overrides
```

### 1. Provider & Version Constraints
`versions.tf` pins minimum versions to guarantee consistent execution:
- OpenTofu / Terraform `>= 1.6.0`
- HashiCorp Google provider `~> 5.0`
- HashiCorp Random provider `>= 3.0`

### 2. Declarative GCP API Enablement
Before any infrastructure module can provision resources, `main.tf` enables all required Google Cloud APIs via `google_project_service` with `disable_on_destroy = false` and `disable_dependent_services = false`:
- `run.googleapis.com` (Cloud Run Admin API)
- `sqladmin.googleapis.com` (Cloud SQL Admin API)
- `storage.googleapis.com` (Cloud Storage API)
- `secretmanager.googleapis.com` (Secret Manager API)
- `iam.googleapis.com` (Identity and Access Management API)

All modules explicitly depend on `google_project_service.services`.

### 3. Module Composition Pipeline
`environments/dev/main.tf` wires the underlying modules together:
1. **IAM Module (`modules/iam`):** Provisions `sa-backend`, `sa-frontend`, and `sa-migrator` service accounts with least-privilege roles.
2. **Cloud SQL Module (`modules/cloudsql`):** Creates the PostgreSQL 16 database instance and registers IAM database users.
3. **Storage Module (`modules/storage`):** Creates the GCS bucket (`<project_id>-assets`) with `force_destroy = true` for easy cleanups in development.
4. **Secret Manager Secrets:**
   - Generates a 32-character random string via `random_password.jwt_secret` and saves it to secret `JWT_SECRET`.
   - Saves the Cloud SQL connection string (`module.cloudsql.instance_connection_name`) to secret `DATABASE_INSTANCE`.
5. **Cloud Run Module (`modules/cloudrun`):** Deploys the frontend and backend services along with the schema migration job, passing database connection strings and bucket names into container environments.

## Deployment Lifecycle & Database Migrations

```
+--------------------+        +--------------------+        +--------------------+
| 1. Apply Infra     | -----> | 2. Run Migrations  | -----> | 3. Verify Services |
|  - tofu apply      |        |  - gcloud run jobs |        |  - frontend_url    |
|  - Enables APIs    |        |    execute         |        |  - backend_url     |
|  - Creates Mod Res |        |    sample-migration|        |                    |
+--------------------+        +--------------------+        +--------------------+
```

### Triggering Schema Migrations
The dev environment exports a helper output `migration_job_execute_command`:
```bash
gcloud run jobs execute sample-migration --region us-central1 --project <project_id>
```
Executing this command launches the `google_cloud_run_v2_job.migration` resource, which runs `alembic upgrade head` under the `sa-migrator` identity before traffic reaches updated application code.

## State Management

By default, local state is excluded from version control via `.gitignore`. For collaborative team environments, state is stored in a remote GCS bucket:
1. A GCS bucket is provisioned with Object Versioning and Uniform Bucket-Level Access.
2. `backend.tf.example` is copied to `backend.tf`:
   ```terraform
   terraform {
     backend "gcs" {
       bucket = "my-dev-tfstate-bucket"
       prefix = "terraform/state/dev"
     }
   }
   ```
3. Running `tofu init -migrate-state` migrates state from local disk to the GCS bucket.

## Testing & Validation Strategy

The repository maintains an automated testing pyramid:

1. **OpenTofu Test Framework (`*.tftest.hcl`):**
   - Located in `modules/*/tests/`.
   - Utilizes `mock_provider "google"` to execute declarative plan assertions without contacting cloud APIs.
   - Asserts port configurations, role assignments, username suffix trimming, and scaling parameters.

2. **Python Unit & Contract Tests (`tests/test_*.py`):**
   - Validates that modules and environment configurations declare all required variables without defaults.
   - Enforces that no static passwords exist anywhere in the code.
   - Enforces that Serverless VPC Access connectors are not introduced.
   - Executes `tofu fmt -check`, `tofu init -backend=false`, and `tofu validate` on all modules and environments.
