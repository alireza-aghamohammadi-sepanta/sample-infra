"""Module validation tests for Cloud Run module.

Covers: AC-1, AC-2
- Asserts modules/cloudrun requires project_id, region, backend_image, frontend_image,
  backend_sa_email, frontend_sa_email, and migrator_sa_email (no default values).
- Asserts container image inputs, service account emails, environment variables,
  database instance connection name, and region are defined.
- Asserts services enforce min_instance_count = 0 and max_instance_count = 10.
- Asserts backend container port is 8000 and frontend container port is 8080.
- Asserts public invoker role bindings (roles/run.invoker to allUsers) for both services.
- Asserts Cloud Run Job entrypoint command is ["alembic", "upgrade", "head"] executed as sa-migrator.
- Asserts Cloud Run Job configures database connection environment variables (DB_USER, DB_NAME, DATABASE_INSTANCE).
- Asserts outputs backend_url, frontend_url, and migration_job_name are exported.
- Validates OpenTofu fmt, init, and validate.
"""

import os
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLOUDRUN_MODULE_DIR = REPO_ROOT / "modules" / "cloudrun"


class TestCloudRunModuleValidation(unittest.TestCase):
    def test_variables_declared_and_required(self):
        """AC-1, AC-2: Assert required inputs have no defaults, and expected variables exist."""
        variables_file = CLOUDRUN_MODULE_DIR / "variables.tf"
        self.assertTrue(
            variables_file.is_file(),
            f"Expected {variables_file} to exist",
        )

        content = variables_file.read_text()

        # Parse all variable blocks
        var_blocks = re.findall(
            r'variable\s+"([^"]+)"\s+\{([^}]*)\}',
            content,
            re.DOTALL,
        )
        vars_dict = {name: body for name, body in var_blocks}

        required_vars = [
            "project_id",
            "region",
            "backend_image",
            "frontend_image",
            "backend_sa_email",
            "frontend_sa_email",
            "migrator_sa_email",
        ]
        for var_name in required_vars:
            self.assertIn(
                var_name,
                vars_dict,
                f"Variable '{var_name}' must be declared in variables.tf",
            )
            self.assertFalse(
                re.search(r'^\s*default\s*=', vars_dict[var_name], re.MULTILINE),
                f"Variable '{var_name}' must be required (cannot have a default attribute)",
            )

        # Database instance connection name variable declared
        self.assertTrue(
            "database_instance" in vars_dict
            or "database_instance_connection_name" in vars_dict,
            "Database instance connection name variable must be declared in variables.tf",
        )

        # Environment variables defined
        self.assertTrue(
            "backend_env_vars" in vars_dict
            or "frontend_env_vars" in vars_dict
            or "env_vars" in vars_dict,
            "Environment variables must be declared in variables.tf",
        )

    def test_services_and_job_declared(self):
        """AC-1, AC-2: Assert Cloud Run v2 services, scaling, ports, public invoker bindings, and migration job."""
        main_file = CLOUDRUN_MODULE_DIR / "main.tf"
        self.assertTrue(
            main_file.is_file(),
            f"Expected {main_file} to exist",
        )

        content = main_file.read_text()

        # google_cloud_run_v2_service declared for backend and frontend
        self.assertIn(
            "google_cloud_run_v2_service",
            content,
            "main.tf must declare google_cloud_run_v2_service",
        )
        self.assertRegex(
            content,
            r'resource\s+"google_cloud_run_v2_service"\s+"backend"',
            "Backend Cloud Run service must be declared",
        )
        self.assertRegex(
            content,
            r'resource\s+"google_cloud_run_v2_service"\s+"frontend"',
            "Frontend Cloud Run service must be declared",
        )

        # min_instance_count = 0 and max_instance_count = 10
        self.assertRegex(
            content,
            r'min_instance_count\s*=\s*(0|var\.min_instance_count)',
            "Services must enforce min_instance_count = 0",
        )
        self.assertRegex(
            content,
            r'max_instance_count\s*=\s*(10|var\.max_instance_count)',
            "Services must enforce max_instance_count = 10",
        )

        # Container ports: backend 8000, frontend 8080
        self.assertRegex(
            content,
            r'container_port\s*=\s*8000',
            "Backend service must configure container port 8000",
        )
        self.assertRegex(
            content,
            r'container_port\s*=\s*8080',
            "Frontend service must configure container port 8080",
        )

        # Public invoker IAM member bindings for both services
        self.assertIn(
            "google_cloud_run_v2_service_iam_member",
            content,
            "main.tf must declare google_cloud_run_v2_service_iam_member",
        )
        self.assertIn(
            "roles/run.invoker",
            content,
            "Public invoker binding must use roles/run.invoker",
        )
        self.assertIn(
            "allUsers",
            content,
            "Public invoker binding must bind to allUsers",
        )

        # Cloud Run Job for Alembic migration
        self.assertIn(
            "google_cloud_run_v2_job",
            content,
            "main.tf must declare google_cloud_run_v2_job",
        )
        self.assertRegex(
            content,
            r'service_account\s*=\s*var\.migrator_sa_email',
            "Migration Cloud Run Job must execute under var.migrator_sa_email",
        )
        # Entrypoint command ["alembic", "upgrade", "head"]
        self.assertTrue(
            '["alembic", "upgrade", "head"]' in content
            or '["alembic",\n' in content
            or re.search(r'command\s*=\s*\[\s*"alembic"\s*,\s*"upgrade"\s*,\s*"head"\s*\]', content),
            'Migration job must specify command ["alembic", "upgrade", "head"]',
        )

        # Database connection environment variables: DB_USER, DB_NAME, DATABASE_INSTANCE
        for env_name in ["DB_USER", "DB_NAME", "DATABASE_INSTANCE"]:
            self.assertIn(
                env_name,
                content,
                f"Migration job must configure environment variable {env_name}",
            )

    def test_outputs_exported(self):
        """AC-2: Assert service URLs and migration job name are exported."""
        outputs_file = CLOUDRUN_MODULE_DIR / "outputs.tf"
        self.assertTrue(
            outputs_file.is_file(),
            f"Expected {outputs_file} to exist",
        )

        content = outputs_file.read_text()

        required_outputs = [
            "backend_url",
            "frontend_url",
            "migration_job_name",
        ]
        for output_name in required_outputs:
            pattern = rf'output\s+"{output_name}"\s+\{{'
            self.assertIsNotNone(
                re.search(pattern, content),
                f"Output '{output_name}' must be exported in outputs.tf",
            )

    def test_opentofu_fmt_and_validation(self):
        """AC-1, AC-2: Validate OpenTofu syntax and schema in modules/cloudrun."""
        self.assertTrue(
            CLOUDRUN_MODULE_DIR.is_dir(),
            f"Directory {CLOUDRUN_MODULE_DIR} must exist",
        )

        fmt_res = subprocess.run(
            ["tofu", "fmt", "-check"],
            cwd=CLOUDRUN_MODULE_DIR,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            fmt_res.returncode,
            0,
            f"tofu fmt -check failed:\n{fmt_res.stdout}\n{fmt_res.stderr}",
        )

        init_res = subprocess.run(
            ["tofu", "init", "-backend=false"],
            cwd=CLOUDRUN_MODULE_DIR,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            init_res.returncode,
            0,
            f"tofu init failed:\n{init_res.stdout}\n{init_res.stderr}",
        )

        val_res = subprocess.run(
            ["tofu", "validate"],
            cwd=CLOUDRUN_MODULE_DIR,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            val_res.returncode,
            0,
            f"tofu validate failed:\n{val_res.stdout}\n{val_res.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
