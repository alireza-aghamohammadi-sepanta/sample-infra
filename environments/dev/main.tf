locals {
  gcp_services = [
    "run.googleapis.com",
    "sqladmin.googleapis.com",
    "storage.googleapis.com",
    "secretmanager.googleapis.com",
    "iam.googleapis.com",
  ]
  bucket_name = var.bucket_name != null ? var.bucket_name : "${var.project_id}-assets"
}

# Declaratively enable required GCP APIs
resource "google_project_service" "services" {
  for_each                   = toset(local.gcp_services)
  project                    = var.project_id
  service                    = each.value
  disable_on_destroy         = false
  disable_dependent_services = false
}

# Module T1: IAM Service Accounts and Role Bindings
module "iam" {
  source     = "../../modules/iam"
  project_id = var.project_id

  depends_on = [google_project_service.services]
}

# Module T2: Cloud SQL PostgreSQL Instance
module "cloudsql" {
  source              = "../../modules/cloudsql"
  project_id          = var.project_id
  region              = var.region
  tier                = var.db_tier
  database_name       = var.database_name
  backend_sa_email    = module.iam.backend_sa_email
  migrator_sa_email   = module.iam.migrator_sa_email
  deletion_protection = false

  depends_on = [google_project_service.services]
}

# Module T3: Google Cloud Storage Bucket for Assets
module "storage" {
  source        = "../../modules/storage"
  project_id    = var.project_id
  region        = var.region
  bucket_name   = local.bucket_name
  force_destroy = true

  depends_on = [google_project_service.services]
}

# Secret Manager: JWT_SECRET (32-character auto-generated random string)
resource "random_password" "jwt_secret" {
  length  = 32
  special = false
}

resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "JWT_SECRET"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "jwt_secret" {
  secret      = google_secret_manager_secret.jwt_secret.id
  secret_data = random_password.jwt_secret.result
}

# Secret Manager: DATABASE_INSTANCE (Cloud SQL instance connection name)
resource "google_secret_manager_secret" "database_instance" {
  secret_id = "DATABASE_INSTANCE"
  project   = var.project_id

  replication {
    auto {}
  }

  depends_on = [google_project_service.services]
}

resource "google_secret_manager_secret_version" "database_instance" {
  secret      = google_secret_manager_secret.database_instance.id
  secret_data = module.cloudsql.instance_connection_name
}

# Module T4: Cloud Run Services and Database Migration Job
module "cloudrun" {
  source                            = "../../modules/cloudrun"
  project_id                        = var.project_id
  region                            = var.region
  backend_image                     = var.backend_image
  frontend_image                    = var.frontend_image
  migrator_image                    = var.migrator_image
  backend_sa_email                  = module.iam.backend_sa_email
  frontend_sa_email                 = module.iam.frontend_sa_email
  migrator_sa_email                 = module.iam.migrator_sa_email
  database_instance                 = module.cloudsql.instance_connection_name
  database_instance_connection_name = module.cloudsql.instance_connection_name
  database_name                     = module.cloudsql.database_name
  backend_db_user                   = module.cloudsql.backend_db_user
  migrator_db_user                  = module.cloudsql.migrator_db_user
  backend_env_vars = {
    GCS_BUCKET_NAME = module.storage.bucket_name
  }
  min_instance_count  = 0
  max_instance_count  = 10
  deletion_protection = false

  depends_on = [google_project_service.services]
}
