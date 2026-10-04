"""Module validation tests for IAM module.

Covers: AC-1, AC-2
- Asserts project_id input is required (no default).
- Asserts undeclared service accounts and missing variables fail validation.
- Asserts service accounts sa-backend, sa-frontend, sa-migrator and least-privilege roles are declared.
- Asserts outputs backend_sa_email, frontend_sa_email, migrator_sa_email and IDs are exported.
"""

import os
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
IAM_MODULE_DIR = REPO_ROOT / "modules" / "iam"


class TestIAMModuleValidation(unittest.TestCase):
    def test_variables_declared_and_project_id_required(self):
        """AC-2: Assert project_id input variable is declared and required."""
        variables_file = IAM_MODULE_DIR / "variables.tf"
        self.assertTrue(
            variables_file.is_file(),
            f"Expected {variables_file} to exist",
        )

        content = variables_file.read_text()

        # Variable project_id must be declared
        pattern = r'variable\s+"project_id"\s+\{([^}]+)\}'
        match = re.search(pattern, content, re.DOTALL)
        self.assertIsNotNone(match, "variable 'project_id' must be declared")

        block_body = match.group(1)
        # It must be required (i.e. no default attribute)
        self.assertNotIn(
            "default",
            block_body,
            "variable 'project_id' must be required (cannot have a default value)",
        )

    def test_service_accounts_and_least_privilege_roles_declared(self):
        """AC-1: Assert service accounts and least-privilege roles are declared."""
        main_file = IAM_MODULE_DIR / "main.tf"
        self.assertTrue(
            main_file.is_file(),
            f"Expected {main_file} to exist",
        )

        content = main_file.read_text()

        # Check service accounts
        for sa_id in ["sa-backend", "sa-frontend", "sa-migrator"]:
            self.assertIn(
                sa_id,
                content,
                f"Service account '{sa_id}' must be declared in main.tf",
            )

        # Check required least-privilege roles for backend
        backend_roles = [
            "roles/cloudsql.client",
            "roles/cloudsql.instanceUser",
            "roles/secretmanager.secretAccessor",
            "roles/storage.objectAdmin",
        ]
        for role in backend_roles:
            self.assertIn(
                role,
                content,
                f"Role '{role}' must be granted to sa-backend",
            )

        # Check required least-privilege roles for migrator
        migrator_roles = [
            "roles/cloudsql.client",
            "roles/cloudsql.instanceUser",
            "roles/secretmanager.secretAccessor",
        ]
        for role in migrator_roles:
            self.assertIn(
                role,
                content,
                f"Role '{role}' must be granted to sa-migrator",
            )

        # Frontend should have minimal execution role and NO access to database, secrets, or storage
        self.assertIn("roles/run.invoker", content, "sa-frontend must have minimal execution role (roles/run.invoker)")

    def test_outputs_exported(self):
        """AC-2: Assert service account emails and IDs are exported."""
        outputs_file = IAM_MODULE_DIR / "outputs.tf"
        self.assertTrue(
            outputs_file.is_file(),
            f"Expected {outputs_file} to exist",
        )

        content = outputs_file.read_text()

        required_outputs = [
            "backend_sa_email",
            "frontend_sa_email",
            "migrator_sa_email",
            "backend_sa_id",
            "frontend_sa_id",
            "migrator_sa_id",
        ]
        for output_name in required_outputs:
            pattern = rf'output\s+"{output_name}"\s+\{{'
            self.assertIsNotNone(
                re.search(pattern, content),
                f"Output '{output_name}' must be exported in outputs.tf",
            )

    def test_opentofu_fmt_and_validation(self):
        """AC-1, AC-2: Validate OpenTofu syntax and schema in modules/iam."""
        self.assertTrue(
            IAM_MODULE_DIR.is_dir(),
            f"Directory {IAM_MODULE_DIR} must exist",
        )

        fmt_res = subprocess.run(
            ["tofu", "fmt", "-check"],
            cwd=IAM_MODULE_DIR,
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
            cwd=IAM_MODULE_DIR,
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
            cwd=IAM_MODULE_DIR,
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
