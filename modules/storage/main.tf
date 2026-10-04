terraform {
  required_version = ">= 1.6.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = ">= 5.0"
    }
  }
}

resource "google_storage_bucket" "default" {
  name                        = var.bucket_name
  project                     = var.project_id
  location                    = coalesce(var.location, var.region)
  storage_class               = var.storage_class
  uniform_bucket_level_access = true
  public_access_prevention    = "enforced"
  force_destroy               = var.force_destroy

  cors {
    origin          = var.cors_origins
    method          = ["GET", "PUT", "OPTIONS"]
    response_header = ["Content-Type", "Content-Length", "ETag", "x-goog-*"]
    max_age_seconds = 3600
  }
}
