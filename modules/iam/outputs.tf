output "backend_sa_email" {
  description = "The email address of the backend service account."
  value       = google_service_account.backend.email
}

output "backend_sa_id" {
  description = "The fully-qualified identifier of the backend service account."
  value       = google_service_account.backend.id
}

output "backend_sa_unique_id" {
  description = "The unique numerical identifier of the backend service account."
  value       = google_service_account.backend.unique_id
}

output "frontend_sa_email" {
  description = "The email address of the frontend service account."
  value       = google_service_account.frontend.email
}

output "frontend_sa_id" {
  description = "The fully-qualified identifier of the frontend service account."
  value       = google_service_account.frontend.id
}

output "frontend_sa_unique_id" {
  description = "The unique numerical identifier of the frontend service account."
  value       = google_service_account.frontend.unique_id
}

output "migrator_sa_email" {
  description = "The email address of the schema migration job service account."
  value       = google_service_account.migrator.email
}

output "migrator_sa_id" {
  description = "The fully-qualified identifier of the schema migration job service account."
  value       = google_service_account.migrator.id
}

output "migrator_sa_unique_id" {
  description = "The unique numerical identifier of the schema migration job service account."
  value       = google_service_account.migrator.unique_id
}
