variable "project_id" {
  description = "The GCP project ID where the Cloud SQL instance is provisioned."
  type        = string
}

variable "region" {
  description = "The GCP region for the Cloud SQL instance."
  type        = string
}

variable "tier" {
  description = "The machine tier / compute shape for the Cloud SQL instance (e.g. db-f1-micro, db-custom-2-7680)."
  type        = string
}

variable "database_name" {
  description = "The name of the default PostgreSQL database to create."
  type        = string
}

variable "backend_sa_email" {
  description = "The service account email of the backend application for Cloud IAM database authentication."
  type        = string
}

variable "migrator_sa_email" {
  description = "The service account email of the schema migration job for Cloud IAM database authentication."
  type        = string
}

variable "instance_name" {
  description = "Optional name override for the Cloud SQL instance. If null, a name derived from database_name is used."
  type        = string
  default     = null
}

variable "database_version" {
  description = "The database engine version."
  type        = string
  default     = "POSTGRES_16"
}

variable "availability_type" {
  description = "The availability type for the instance (ZONAL for single-zone or REGIONAL for HA)."
  type        = string
  default     = "ZONAL"
}

variable "deletion_protection" {
  description = "Whether deletion protection is enabled for the Cloud SQL instance."
  type        = bool
  default     = false
}

variable "authorized_networks" {
  description = "List of authorized IPv4 CIDR blocks permitted to connect directly to the Cloud SQL instance."
  type = list(object({
    name  = optional(string)
    value = string
  }))
  default = []
}
