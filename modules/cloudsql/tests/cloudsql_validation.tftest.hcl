mock_provider "google" {}

variables {
  project_id        = "test-project-id"
  region            = "us-central1"
  tier              = "db-f1-micro"
  database_name     = "testdb"
  backend_sa_email  = "sa-backend@test-project-id.iam.gserviceaccount.com"
  migrator_sa_email = "sa-migrator@test-project-id.iam.gserviceaccount.com"
}

run "verify_cloudsql_outputs" {
  command = plan

  assert {
    condition     = output.database_name == "testdb"
    error_message = "database_name output must match var.database_name"
  }

  assert {
    condition     = output.backend_db_user == "sa-backend@test-project-id.iam"
    error_message = "backend_db_user output must trim .gserviceaccount.com"
  }

  assert {
    condition     = output.migrator_db_user == "sa-migrator@test-project-id.iam"
    error_message = "migrator_db_user output must trim .gserviceaccount.com"
  }
}
