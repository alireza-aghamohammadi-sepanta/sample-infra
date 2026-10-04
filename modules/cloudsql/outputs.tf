output "instance_connection_name" {
  description = "The connection name of the Cloud SQL instance (format: project:region:instance)."
  value       = google_sql_database_instance.default.connection_name
}

output "instance_name" {
  description = "The name of the Cloud SQL instance."
  value       = google_sql_database_instance.default.name
}

output "public_ip_address" {
  description = "The public IPv4 address assigned for the Cloud SQL instance."
  value       = google_sql_database_instance.default.public_ip_address
}

output "database_name" {
  description = "The name of the default relational database."
  value       = google_sql_database.default.name
}

output "backend_db_user" {
  description = "The IAM database username for the backend service account."
  value       = google_sql_user.backend.name
}

output "migrator_db_user" {
  description = "The IAM database username for the schema migration job service account."
  value       = google_sql_user.migrator.name
}
