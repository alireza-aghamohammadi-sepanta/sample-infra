mock_provider "google" {}

variables {
  project_id = "test-project-id"
}

run "verify_iam_outputs" {
  command = plan

  assert {
    condition     = output.backend_sa_email != ""
    error_message = "backend_sa_email output must not be empty"
  }

  assert {
    condition     = output.frontend_sa_email != ""
    error_message = "frontend_sa_email output must not be empty"
  }

  assert {
    condition     = output.migrator_sa_email != ""
    error_message = "migrator_sa_email output must not be empty"
  }
}
