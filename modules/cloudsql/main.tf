terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

resource "google_sql_database_instance" "default" {
  name                = var.instance_name != null ? var.instance_name : "${var.database_name}-instance"
  project             = var.project_id
  region              = var.region
  database_version    = var.database_version
  deletion_protection = var.deletion_protection

  settings {
    tier              = var.tier
    availability_type = var.availability_type
    disk_type         = "PD_SSD"
    disk_autoresize   = true

    ip_configuration {
      ipv4_enabled = true

      dynamic "authorized_networks" {
        for_each = var.authorized_networks
        content {
          name  = lookup(authorized_networks.value, "name", null)
          value = authorized_networks.value.value
        }
      }
    }

    database_flags {
      name  = "cloudsql.iam_authentication"
      value = "on"
    }
  }
}

resource "google_sql_database" "default" {
  name     = var.database_name
  instance = google_sql_database_instance.default.name
  project  = var.project_id
}

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
