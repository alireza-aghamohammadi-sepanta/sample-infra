variable "project_id" {
  description = "The GCP project ID where Cloud Run resources are provisioned."
  type        = string
}

variable "region" {
  description = "The GCP region for the Cloud Run resources."
  type        = string
}

variable "backend_image" {
  description = "The container image URL for the backend Cloud Run service."
  type        = string
}

variable "frontend_image" {
  description = "The container image URL for the frontend Cloud Run service."
  type        = string
}

variable "migrator_image" {
  description = "The container image URL for the schema migration job. Defaults to backend_image if null."
  type        = string
  default     = null
}

variable "backend_sa_email" {
  description = "The service account email for the backend Cloud Run service."
  type        = string
}

variable "frontend_sa_email" {
  description = "The service account email for the frontend Cloud Run service."
  type        = string
}

variable "migrator_sa_email" {
  description = "The service account email for the schema migration Cloud Run job."
  type        = string
}

variable "database_instance" {
  description = "The Cloud SQL instance connection name (format: project:region:instance)."
  type        = string
  default     = ""
}

variable "database_instance_connection_name" {
  description = "Alternative input for the Cloud SQL instance connection name."
  type        = string
  default     = null
}

variable "database_name" {
  description = "The name of the PostgreSQL database."
  type        = string
  default     = "postgres"
}

variable "backend_db_user" {
  description = "The IAM database username for the backend service. Defaults to the trimmed backend_sa_email."
  type        = string
  default     = null
}

variable "migrator_db_user" {
  description = "The IAM database username for the schema migration job. Defaults to the trimmed migrator_sa_email."
  type        = string
  default     = null
}

variable "backend_env_vars" {
  description = "Additional environment variables for the backend Cloud Run service."
  type        = map(string)
  default     = {}
}

variable "frontend_env_vars" {
  description = "Additional environment variables for the frontend Cloud Run service."
  type        = map(string)
  default     = {}
}

variable "migration_env_vars" {
  description = "Additional environment variables for the schema migration Cloud Run job."
  type        = map(string)
  default     = {}
}

variable "backend_service_name" {
  description = "The name of the backend Cloud Run service."
  type        = string
  default     = "sample-backend"
}

variable "frontend_service_name" {
  description = "The name of the frontend Cloud Run service."
  type        = string
  default     = "sample-frontend"
}

variable "migration_job_name" {
  description = "The name of the Alembic migration Cloud Run job."
  type        = string
  default     = "sample-migration"
}

variable "min_instance_count" {
  description = "Minimum number of container instances for Cloud Run services."
  type        = number
  default     = 0
}

variable "max_instance_count" {
  description = "Maximum number of container instances for Cloud Run services."
  type        = number
  default     = 10
}

variable "deletion_protection" {
  description = "Whether deletion protection is enabled for Cloud Run services and jobs."
  type        = bool
  default     = false
}
