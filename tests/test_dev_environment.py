"""Environment configuration tests for dev environment.

Covers: AC-1, AC-2, AC-3, AC-4
- Asserts environments/dev declares required APIs with disable_on_destroy = false:
  run.googleapis.com, sqladmin.googleapis.com, storage.googleapis.com,
  secretmanager.googleapis.com, iam.googleapis.com.
- Asserts Secret Manager secret JWT_SECRET provisioned with random_password (32 chars) and version.
- Asserts Secret Manager secret DATABASE_INSTANCE provisioned with Cloud SQL connection name and version.
- Asserts container image variables default to us-docker.pkg.dev/cloudrun/container/hello.
- Asserts modules iam, cloudsql, storage, and cloudrun are wired together.
- Asserts outputs for frontend/backend URLs, Cloud SQL connection name, GCS bucket name, and migration job execute command.
- Asserts backend.tf.example and terraform.tfvars.example exist and are populated.
- Asserts no static passwords and no Serverless VPC Access connector resources exist.
- Validates OpenTofu fmt, init, and validate.
"""

import os
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEV_ENV_DIR = REPO_ROOT / "environments" / "dev"


class TestDevEnvironmentValidation(unittest.TestCase):
    def test_versions_file_configuration(self):
        """AC-1: Assert versions.tf declares OpenTofu and Google provider version constraints (~> 5.0)."""
        versions_file = DEV_ENV_DIR / "versions.tf"
        self.assertTrue(
            versions_file.is_file(),
            f"Expected {versions_file} to exist",
        )
        content = versions_file.read_text()

        # Check required_version
        self.assertRegex(
            content,
            r'required_version\s*=\s*"[^"]*"',
            "required_version must be defined in versions.tf",
        )

        # Check google provider version constraint ~> 5.0
        self.assertIn(
            "google",
            content,
            "google provider must be declared in required_providers",
        )
        self.assertRegex(
            content,
            r'version\s*=\s*"~>\s*5\.0"',
            "Google provider version constraint must be ~> 5.0",
        )

    def test_variables_and_image_defaults(self):
        """AC-1, AC-2: Assert variables.tf defines inputs and defaults container images to us-docker.pkg.dev/cloudrun/container/hello."""
        variables_file = DEV_ENV_DIR / "variables.tf"
        self.assertTrue(
            variables_file.is_file(),
            f"Expected {variables_file} to exist",
        )
        content = variables_file.read_text()

        var_blocks = re.findall(
            r'variable\s+"([^"]+)"\s+\{([^}]*)\}',
            content,
            re.DOTALL,
        )
        vars_dict = {name: body for name, body in var_blocks}

        # project_id must be declared and required (no default)
        self.assertIn("project_id", vars_dict, "project_id must be declared in variables.tf")
        self.assertFalse(
            re.search(r'^\s*default\s*=', vars_dict["project_id"], re.MULTILINE),
            "project_id must be required without default",
        )

        # Container images must default to us-docker.pkg.dev/cloudrun/container/hello
        default_hello = "us-docker.pkg.dev/cloudrun/container/hello"
        for img_var in ["backend_image", "frontend_image"]:
            self.assertIn(img_var, vars_dict, f"Variable '{img_var}' must be declared")
            self.assertIn(
                default_hello,
                vars_dict[img_var],
                f"Variable '{img_var}' must default to '{default_hello}'",
            )

    def test_required_apis_declared_with_disable_on_destroy_false(self):
        """AC-1, AC-3: Assert required APIs are declared with disable_on_destroy = false."""
        main_file = DEV_ENV_DIR / "main.tf"
        self.assertTrue(
            main_file.is_file(),
            f"Expected {main_file} to exist",
        )
        content = main_file.read_text()

        required_apis = [
            "run.googleapis.com",
            "sqladmin.googleapis.com",
            "storage.googleapis.com",
            "secretmanager.googleapis.com",
            "iam.googleapis.com",
        ]
        for api in required_apis:
            self.assertIn(
                api,
                content,
                f"API '{api}' must be declared in {main_file}",
            )

        # Assert disable_on_destroy = false is declared
        self.assertRegex(
            content,
            r'disable_on_destroy\s*=\s*false',
            "disable_on_destroy must be set to false for google_project_service resources",
        )

    def test_secret_manager_secrets_and_versions(self):
        """AC-1, AC-4: Assert JWT_SECRET and DATABASE_INSTANCE secrets are provisioned with active versions."""
        main_file = DEV_ENV_DIR / "main.tf"
        self.assertTrue(
            main_file.is_file(),
            f"Expected {main_file} to exist",
        )
        content = main_file.read_text()

        # Random password with length 32
        self.assertIn("random_password", content, "random_password resource must be declared")
        self.assertRegex(
            content,
            r'length\s*=\s*32',
            "random_password length must be 32",
        )

        # Secret Manager resources for JWT_SECRET and DATABASE_INSTANCE
        self.assertIn("JWT_SECRET", content, "JWT_SECRET secret must be declared")
        self.assertIn("DATABASE_INSTANCE", content, "DATABASE_INSTANCE secret must be declared")

        # Secret versions
        self.assertIn(
            "google_secret_manager_secret_version",
            content,
            "google_secret_manager_secret_version resources must be declared",
        )

    def test_module_wiring_t1_to_t4(self):
        """AC-1, AC-2, AC-3: Assert modules iam, cloudsql, storage, and cloudrun are wired."""
        main_file = DEV_ENV_DIR / "main.tf"
        self.assertTrue(
            main_file.is_file(),
            f"Expected {main_file} to exist",
        )
        content = main_file.read_text()

        # Check module invocations
        for module_name in ["iam", "cloudsql", "storage", "cloudrun"]:
            self.assertRegex(
                content,
                rf'module\s+"{module_name}"\s+\{{',
                f"Module '{module_name}' must be invoked in {main_file}",
            )

        # Check cross-module references:
        # cloudsql must use IAM service accounts
        self.assertIn("module.iam.backend_sa_email", content)
        self.assertIn("module.iam.migrator_sa_email", content)

        # cloudrun must use IAM service accounts and Cloud SQL connection name
        self.assertIn("module.iam.frontend_sa_email", content)
        self.assertIn("module.cloudsql.instance_connection_name", content)

    def test_outputs_declared(self):
        """AC-1: Assert outputs export Cloud Run URLs, Cloud SQL connection, GCS bucket, and migration command."""
        outputs_file = DEV_ENV_DIR / "outputs.tf"
        self.assertTrue(
            outputs_file.is_file(),
            f"Expected {outputs_file} to exist",
        )
        content = outputs_file.read_text()

        output_blocks = re.findall(r'output\s+"([^"]+)"\s+\{', content)

        self.assertIn("backend_url", output_blocks, "backend_url output must be exported")
        self.assertIn("frontend_url", output_blocks, "frontend_url output must be exported")
        self.assertTrue(
            "instance_connection_name" in output_blocks or "cloudsql_connection_name" in output_blocks,
            "Cloud SQL instance connection name output must be exported",
        )
        self.assertTrue(
            "bucket_name" in output_blocks or "gcs_bucket_name" in output_blocks,
            "GCS bucket name output must be exported",
        )
        self.assertTrue(
            "migration_job_execute_command" in output_blocks or "migration_execute_command" in output_blocks,
            "Migration job execute command output must be exported",
        )

    def test_example_files_exist(self):
        """AC-1: Assert backend.tf.example and terraform.tfvars.example exist and are populated."""
        backend_example = DEV_ENV_DIR / "backend.tf.example"
        self.assertTrue(
            backend_example.is_file(),
            f"Expected {backend_example} to exist",
        )
        backend_content = backend_example.read_text()
        self.assertIn('backend "gcs"', backend_content)

        tfvars_example = DEV_ENV_DIR / "terraform.tfvars.example"
        self.assertTrue(
            tfvars_example.is_file(),
            f"Expected {tfvars_example} to exist",
        )
        tfvars_content = tfvars_example.read_text()
        self.assertIn("project_id", tfvars_content)

    def test_invariants(self):
        """Assert zero static database passwords and no Serverless VPC Access connector."""
        tf_files = list(DEV_ENV_DIR.glob("*.tf"))
        self.assertTrue(len(tf_files) > 0, "Terraform files must exist in dev environment")

        for tf_file in tf_files:
            content = tf_file.read_text()
            self.assertNotIn(
                "google_vpc_access_connector",
                content,
                f"No Serverless VPC Access connector allowed in dev: found in {tf_file}",
            )
            self.assertNotRegex(
                content,
                r'password\s*=\s*"[^"]+"',
                f"Static password found in {tf_file}",
            )

    def test_tofu_fmt_init_validate(self):
        """Validate dev environment configuration with OpenTofu."""
        self.assertTrue(DEV_ENV_DIR.is_dir(), f"{DEV_ENV_DIR} must exist")

        fmt_res = subprocess.run(
            ["tofu", "fmt", "-check"],
            cwd=DEV_ENV_DIR,
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
            cwd=DEV_ENV_DIR,
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
            cwd=DEV_ENV_DIR,
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
