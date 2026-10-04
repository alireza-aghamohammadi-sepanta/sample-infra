terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

resource "google_service_account" "backend" {
  account_id   = "sa-backend"
  display_name = "Backend Service Account"
  project      = var.project_id
}

resource "google_service_account" "frontend" {
  account_id   = "sa-frontend"
  display_name = "Frontend Service Account"
  project      = var.project_id
}

resource "google_service_account" "migrator" {
  account_id   = "sa-migrator"
  display_name = "Schema Migration Job Service Account"
  project      = var.project_id
}

locals {
  backend_roles = [
    "roles/cloudsql.client",
    "roles/cloudsql.instanceUser",
    "roles/secretmanager.secretAccessor",
    "roles/storage.objectAdmin",
  ]

  migrator_roles = [
    "roles/cloudsql.client",
    "roles/cloudsql.instanceUser",
    "roles/secretmanager.secretAccessor",
  ]

  frontend_roles = [
    "roles/run.invoker",
  ]
}

resource "google_project_iam_member" "backend" {
  for_each = toset(local.backend_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.backend.email}"
}

resource "google_project_iam_member" "migrator" {
  for_each = toset(local.migrator_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.migrator.email}"
}

resource "google_project_iam_member" "frontend" {
  for_each = toset(local.frontend_roles)
  project  = var.project_id
  role     = each.value
  member   = "serviceAccount:${google_service_account.frontend.email}"
}
