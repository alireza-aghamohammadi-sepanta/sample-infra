mock_provider "google" {}

variables {
  bucket_name = "test-asset-bucket"
  region      = "europe-west1"
}

run "verify_storage_outputs" {
  command = plan

  assert {
    condition     = output.bucket_name == "test-asset-bucket"
    error_message = "bucket_name output must match var.bucket_name"
  }

  assert {
    condition     = output.bucket_url != ""
    error_message = "bucket_url output must not be empty"
  }
}
