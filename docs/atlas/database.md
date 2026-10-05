---
type: concept
title: Relational Database Infrastructure
summary: Managed Cloud SQL PostgreSQL provisioning with IAM database authentication and zero static passwords.
related: ["architecture.md", "compute.md", "security.md", "networking.md"]
source_paths: ["modules/cloudsql/main.tf", "modules/cloudsql/variables.tf", "modules/cloudsql/outputs.tf", "modules/cloudsql/tests/cloudsql_validation.tftest.hcl", "tests/test_cloudsql_module.py"]
---

# Relational Database Infrastructure

The relational persistence tier is managed by `modules/cloudsql`. It automates the provisioning of Google Cloud SQL for PostgreSQL instances with strict security baselines, automatic disk management, and native Cloud IAM database authentication.

## Engine & Instance Specifications

- **Database Engine:** PostgreSQL 16 (`POSTGRES_16` default in `var.database_version`).
- **Storage Profile:** SSD persistent storage (`PD_SSD`) with dynamic auto-resize (`disk_autoresize = true`).
- **Availability:** Configurable via `availability_type` (`ZONAL` default for development, `REGIONAL` for high-availability production environments).
- **Network Interface:** Public IPv4 connectivity enabled (`ipv4_enabled = true`) under `ip_configuration`, allowing connections via Cloud SQL Connector and optional CIDR ranges specified in `var.authorized_networks`. No Serverless VPC Access connector is required.
- **Deletion Protection:** Configurable boolean (`deletion_protection = false` by default for development environments).

## Passwordless IAM Authentication

A core security tenet of the Cloud SQL module is the total absence of static database passwords:
- No `password` or `root_password` attributes exist in any resource declaration or variable block.
- The instance enables IAM authentication flag `cloudsql.iam_authentication = "on"`.
- Dedicated `google_sql_user` resources are provisioned for both the application runtime and schema migration workloads:

```terraform
resource "google_sql_user" "backend" {
  name     = trimsuffix(var.backend_sa_email, ".gserviceaccount.com")
  instance = google_sql_database_instance.default.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
  project  = var.project_id
}

resource "google_sql_user" "migrator" {
  name     = trimsuffix(var.migrator_sa_email, ".gserviceaccount.com")
  instance = google_sql_database_instance.default.name
  type     = "CLOUD_IAM_SERVICE_ACCOUNT"
  project  = var.project_id
}
```

Google Cloud SQL requires that IAM database usernames omit the `.gserviceaccount.com` domain suffix (e.g. `sa-backend@project-id.iam`). The module handles this normalization automatically via `trimsuffix`.

## Database Provisioning

The default relational database schema is created via `google_sql_database.default` using the name supplied in `var.database_name` (e.g. `sampledb` or `postgres`).

```
+-----------------------------------+             +----------------------------------+
| Backend Service Account           |             | Google Cloud SQL Instance        |
| (sa-backend@proj.iam.gservice)    |             | (PostgreSQL 16, PD_SSD)          |
+-----------------+-----------------+             +-----------------+----------------+
                  |                                                 ^
                  | 1. Cloud SQL Connector Request                  |
                  v                                                 |
+-----------------------------------+                               |
| Cloud SQL Admin API               |                               |
| - Verifies IAM DB User Permission |                               |
| - Issues Ephemeral mTLS Cert      |                               |
+-----------------+-----------------+                               |
                  |                                                 |
                  | 2. Connect over TLS / Port 5432                 |
                  +-------------------------------------------------+
```

## Module Inputs & Outputs

### Required Input Variables
- `project_id` (string): GCP project ID.
- `region` (string): GCP region (e.g. `us-central1`).
- `tier` (string): Machine shape (e.g. `db-f1-micro` for dev, `db-custom-2-7680` for production).
- `database_name` (string): Relational database name.
- `backend_sa_email` (string): Backend application service account email.
- `migrator_sa_email` (string): Migration job service account email.

### Optional Input Variables
- `instance_name` (string, default: `null`): Custom instance name override (defaults to `"${var.database_name}-instance"`).
- `database_version` (string, default: `"POSTGRES_16"`): PostgreSQL engine version.
- `availability_type` (string, default: `"ZONAL"`): `ZONAL` or `REGIONAL`.
- `deletion_protection` (bool, default: `false`): Deletion protection toggle.
- `authorized_networks` (list(object), default: `[]`): Authorized CIDR blocks for direct connections.

### Module Outputs
- `instance_connection_name`: Full connection string formatted as `project:region:instance`.
- `instance_name`: The Cloud SQL instance name.
- `public_ip_address`: Assigned public IPv4 address.
- `database_name`: Created database name.
- `backend_db_user`: The trimmed IAM database username for the backend.
- `migrator_db_user`: The trimmed IAM database username for the migration job.

## Validation & Testing

- **OpenTofu Test Suite** (`modules/cloudsql/tests/cloudsql_validation.tftest.hcl`): Mocks the Google provider to verify database name propagation and IAM username suffix trimming.
- **Python Integration Tests** (`tests/test_cloudsql_module.py`): Validates required inputs without defaults, ensures static passwords are omitted, confirms SSD storage and auto-resize, verifies `cloudsql.iam_authentication` flag, and tests formatting/validation via OpenTofu.
