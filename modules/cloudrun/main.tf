terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

locals {
  database_instance = var.database_instance_connection_name != null ? var.database_instance_connection_name : var.database_instance
  backend_db_user   = var.backend_db_user != null ? var.backend_db_user : trimsuffix(var.backend_sa_email, ".gserviceaccount.com")
  migrator_db_user  = var.migrator_db_user != null ? var.migrator_db_user : trimsuffix(var.migrator_sa_email, ".gserviceaccount.com")
  migrator_image    = var.migrator_image != null ? var.migrator_image : var.backend_image
}

resource "google_cloud_run_v2_service" "backend" {
  name     = var.backend_service_name
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = var.backend_sa_email

    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
    }

    containers {
      image = var.backend_image

      ports {
        container_port = 8000
      }

      env {
        name  = "DATABASE_INSTANCE"
        value = local.database_instance
      }

      env {
        name  = "DB_USER"
        value = local.backend_db_user
      }

      env {
        name  = "DB_NAME"
        value = var.database_name
      }

      env {
        name  = "GCP_PROJECT_ID"
        value = var.project_id
      }

      dynamic "env" {
        for_each = var.backend_env_vars
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "backend_invoker" {
  project  = google_cloud_run_v2_service.backend.project
  location = google_cloud_run_v2_service.backend.location
  name     = google_cloud_run_v2_service.backend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_service" "frontend" {
  name     = var.frontend_service_name
  location = var.region
  project  = var.project_id
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = var.frontend_sa_email

    scaling {
      min_instance_count = var.min_instance_count
      max_instance_count = var.max_instance_count
    }

    containers {
      image = var.frontend_image

      ports {
        container_port = 8080
      }

      dynamic "env" {
        for_each = var.frontend_env_vars
        content {
          name  = env.key
          value = env.value
        }
      }
    }
  }
}

resource "google_cloud_run_v2_service_iam_member" "frontend_invoker" {
  project  = google_cloud_run_v2_service.frontend.project
  location = google_cloud_run_v2_service.frontend.location
  name     = google_cloud_run_v2_service.frontend.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

resource "google_cloud_run_v2_job" "migration" {
  name     = var.migration_job_name
  location = var.region
  project  = var.project_id

  template {
    template {
      service_account = var.migrator_sa_email

      containers {
        image   = local.migrator_image
        command = ["alembic", "upgrade", "head"]

        env {
          name  = "DATABASE_INSTANCE"
          value = local.database_instance
        }

        env {
          name  = "DB_USER"
          value = local.migrator_db_user
        }

        env {
          name  = "DB_NAME"
          value = var.database_name
        }

        dynamic "env" {
          for_each = var.migration_env_vars
          content {
            name  = env.key
            value = env.value
          }
        }
      }
    }
  }
}
