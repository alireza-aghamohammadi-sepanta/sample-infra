variable "bucket_name" {
  description = "The name of the Google Cloud Storage bucket."
  type        = string
}

variable "region" {
  description = "The GCP region for the Google Cloud Storage bucket."
  type        = string
}

variable "location" {
  description = "The location of the bucket. Defaults to var.region if null."
  type        = string
  default     = null
}

variable "storage_class" {
  description = "The storage class of the bucket (e.g. STANDARD, NEARLINE, COLDLINE, ARCHIVE)."
  type        = string
  default     = "STANDARD"
}

variable "cors_origins" {
  description = "Allowed origins for CORS requests."
  type        = list(string)
  default = [
    "https://*.run.app",
    "https://sample-app.example.com",
    "http://localhost:5173",
  ]
}

variable "project_id" {
  description = "The GCP project ID in which the bucket is created."
  type        = string
  default     = null
}

variable "force_destroy" {
  description = "When deleting a bucket, this boolean option will delete all contained objects."
  type        = bool
  default     = false
}
