output "backend_url" {
  description = "The public URL of the backend Cloud Run service."
  value       = google_cloud_run_v2_service.backend.uri
}

output "frontend_url" {
  description = "The public URL of the frontend Cloud Run service."
  value       = google_cloud_run_v2_service.frontend.uri
}

output "migration_job_name" {
  description = "The name of the Alembic migration Cloud Run job."
  value       = google_cloud_run_v2_job.migration.name
}

output "backend_service_name" {
  description = "The name of the backend Cloud Run service."
  value       = google_cloud_run_v2_service.backend.name
}

output "frontend_service_name" {
  description = "The name of the frontend Cloud Run service."
  value       = google_cloud_run_v2_service.frontend.name
}

output "backend_service_id" {
  description = "The unique identifier of the backend Cloud Run service."
  value       = google_cloud_run_v2_service.backend.id
}

output "frontend_service_id" {
  description = "The unique identifier of the frontend Cloud Run service."
  value       = google_cloud_run_v2_service.frontend.id
}

output "migration_job_id" {
  description = "The unique identifier of the Alembic migration Cloud Run job."
  value       = google_cloud_run_v2_job.migration.id
}
