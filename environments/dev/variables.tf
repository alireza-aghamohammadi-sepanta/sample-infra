variable "project_id" {
  description = "The GCP project ID to deploy resources into."
  type        = string
}

variable "region" {
  description = "The GCP region to deploy resources into."
  type        = string
  default     = "us-central1"
}

variable "backend_image" {
  description = "The container image URL for the backend Cloud Run service."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "frontend_image" {
  description = "The container image URL for the frontend Cloud Run service."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "migrator_image" {
  description = "The container image URL for the schema migration job."
  type        = string
  default     = "us-docker.pkg.dev/cloudrun/container/hello"
}

variable "database_name" {
  description = "The name of the default PostgreSQL database."
  type        = string
  default     = "sampledb"
}

variable "db_tier" {
  description = "The machine tier / compute shape for the Cloud SQL instance."
  type        = string
  default     = "db-f1-micro"
}

variable "bucket_name" {
  description = "The name of the Google Cloud Storage bucket for assets. If omitted, defaults to <project_id>-assets."
  type        = string
  default     = null
}
