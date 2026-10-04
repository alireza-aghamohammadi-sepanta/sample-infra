output "bucket_name" {
  description = "The name of the Google Cloud Storage bucket."
  value       = google_storage_bucket.default.name
}

output "bucket_url" {
  description = "The base URL of the Google Cloud Storage bucket."
  value       = google_storage_bucket.default.url
}
