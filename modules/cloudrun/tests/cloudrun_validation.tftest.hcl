mock_provider "google" {}

variables {
  project_id        = "test-project-id"
  region            = "us-central1"
  backend_image     = "us-central1-docker.pkg.dev/test-project-id/repo/backend:latest"
  frontend_image    = "us-central1-docker.pkg.dev/test-project-id/repo/frontend:latest"
  backend_sa_email  = "sa-backend@test-project-id.iam.gserviceaccount.com"
  frontend_sa_email = "sa-frontend@test-project-id.iam.gserviceaccount.com"
  migrator_sa_email = "sa-migrator@test-project-id.iam.gserviceaccount.com"
  database_instance = "test-project-id:us-central1:test-instance"
  database_name     = "testdb"
}

run "verify_cloudrun_configuration" {
  command = plan

  assert {
    condition     = google_cloud_run_v2_service.backend.template[0].scaling[0].min_instance_count == 0
    error_message = "backend min_instance_count must be 0"
  }

  assert {
    condition     = google_cloud_run_v2_service.backend.template[0].scaling[0].max_instance_count == 10
    error_message = "backend max_instance_count must be 10"
  }

  assert {
    condition     = google_cloud_run_v2_service.frontend.template[0].scaling[0].min_instance_count == 0
    error_message = "frontend min_instance_count must be 0"
  }

  assert {
    condition     = google_cloud_run_v2_service.frontend.template[0].scaling[0].max_instance_count == 10
    error_message = "frontend max_instance_count must be 10"
  }

  assert {
    condition     = google_cloud_run_v2_service.backend.template[0].containers[0].ports[0].container_port == 8000
    error_message = "backend container port must be 8000"
  }

  assert {
    condition     = google_cloud_run_v2_service.frontend.template[0].containers[0].ports[0].container_port == 8080
    error_message = "frontend container port must be 8080"
  }

  assert {
    condition     = google_cloud_run_v2_service_iam_member.backend_invoker.role == "roles/run.invoker" && google_cloud_run_v2_service_iam_member.backend_invoker.member == "allUsers"
    error_message = "backend service must bind roles/run.invoker to allUsers"
  }

  assert {
    condition     = google_cloud_run_v2_service_iam_member.frontend_invoker.role == "roles/run.invoker" && google_cloud_run_v2_service_iam_member.frontend_invoker.member == "allUsers"
    error_message = "frontend service must bind roles/run.invoker to allUsers"
  }

  assert {
    condition     = google_cloud_run_v2_job.migration.template[0].template[0].service_account == "sa-migrator@test-project-id.iam.gserviceaccount.com"
    error_message = "migration job service_account must match migrator_sa_email"
  }

  assert {
    condition     = google_cloud_run_v2_job.migration.template[0].template[0].containers[0].command == tolist(["alembic", "upgrade", "head"])
    error_message = "migration job command must be ['alembic', 'upgrade', 'head']"
  }

  assert {
    condition     = output.migration_job_name == "sample-migration"
    error_message = "migration_job_name output must match job name"
  }
}
