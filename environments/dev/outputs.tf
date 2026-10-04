output "backend_url" {
  description = "The public URL of the backend Cloud Run service."
  value       = module.cloudrun.backend_url
}

output "frontend_url" {
  description = "The public URL of the frontend Cloud Run service."
  value       = module.cloudrun.frontend_url
}

output "instance_connection_name" {
  description = "The connection name of the Cloud SQL instance (format: project:region:instance)."
  value       = module.cloudsql.instance_connection_name
}

output "cloudsql_connection_name" {
  description = "Alias for the Cloud SQL instance connection name."
  value       = module.cloudsql.instance_connection_name
}

output "bucket_name" {
  description = "The name of the Google Cloud Storage bucket for assets."
  value       = module.storage.bucket_name
}

output "gcs_bucket_name" {
  description = "Alias for the Google Cloud Storage bucket name."
  value       = module.storage.bucket_name
}

output "migration_job_name" {
  description = "The name of the schema migration Cloud Run job."
  value       = module.cloudrun.migration_job_name
}

output "migration_job_execute_command" {
  description = "The gcloud CLI command to trigger the database migration Cloud Run job."
  value       = "gcloud run jobs execute ${module.cloudrun.migration_job_name} --region ${var.region} --project ${var.project_id}"
}
