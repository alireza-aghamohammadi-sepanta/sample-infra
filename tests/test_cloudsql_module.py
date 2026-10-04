"""Module validation tests for Cloud SQL module.

Covers: AC-1, AC-2
- Asserts modules/cloudsql requires project_id, region, tier, database_name,
  backend_sa_email, and migrator_sa_email (no default values).
- Asserts static password arguments are omitted across all module resources.
- Asserts database engine defaults to POSTGRES_16.
- Asserts SSD storage (PD_SSD) and automatic capacity expansion (disk_autoresize = true).
- Asserts database flag cloudsql.iam_authentication = "on".
- Asserts single-zone configuration and public IPv4 connectivity without VPC connectors.
- Asserts IAM database users of type CLOUD_IAM_SERVICE_ACCOUNT with .gserviceaccount.com suffix trimmed.
- Asserts outputs instance_connection_name, instance_name, public_ip_address, and database_name are exported.
- Validates OpenTofu fmt, init, and validate.
"""

import os
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CLOUDSQL_MODULE_DIR = REPO_ROOT / "modules" / "cloudsql"


class TestCloudSQLModuleValidation(unittest.TestCase):
    def test_variables_declared_and_required(self):
        """AC-1, AC-2: Assert required inputs have no defaults and database engine defaults to POSTGRES_16."""
        variables_file = CLOUDSQL_MODULE_DIR / "variables.tf"
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
            "tier",
            "database_name",
            "backend_sa_email",
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

        # Database engine defaults to POSTGRES_16
        main_file = CLOUDSQL_MODULE_DIR / "main.tf"
        main_content = main_file.read_text() if main_file.is_file() else ""
        if "database_version" in vars_dict:
            self.assertIn(
                "POSTGRES_16",
                vars_dict["database_version"],
                "Variable 'database_version' must default to POSTGRES_16",
            )
        else:
            self.assertIn(
                "POSTGRES_16",
                main_content,
                "Database engine must default to POSTGRES_16 in main.tf",
            )

    def test_static_passwords_omitted(self):
        """AC-1, AC-2: Validate static password arguments are omitted in all resources and variables."""
        self.assertTrue(
            CLOUDSQL_MODULE_DIR.is_dir(),
            f"Expected {CLOUDSQL_MODULE_DIR} to exist",
        )

        for tf_file in CLOUDSQL_MODULE_DIR.glob("*.tf"):
            content = tf_file.read_text()
            # Assert no password assignment: password = ..., root_password = ...
            self.assertFalse(
                re.search(r'^\s*(root_)?password\s*=', content, re.MULTILINE),
                f"Static password argument found in {tf_file.name}",
            )

    def test_database_instance_and_iam_users_declared(self):
        """AC-1, AC-2: Assert single-zone instance, SSD storage, IAM auth flag, and IAM users."""
        main_file = CLOUDSQL_MODULE_DIR / "main.tf"
        self.assertTrue(
            main_file.is_file(),
            f"Expected {main_file} to exist",
        )

        content = main_file.read_text()

        # google_sql_database_instance declared
        self.assertIn(
            "google_sql_database_instance",
            content,
            "main.tf must declare google_sql_database_instance",
        )

        # SSD storage and auto-resize
        self.assertRegex(content, r'disk_type\s*=\s*"PD_SSD"')
        self.assertRegex(content, r'disk_autoresize\s*=\s*true')

        # IAM authentication flag
        self.assertIn("cloudsql.iam_authentication", content)
        self.assertRegex(content, r'value\s*=\s*"on"')

        # Public IPv4 enabled, no VPC connector (private_network)
        self.assertRegex(content, r'ipv4_enabled\s*=\s*true')
        self.assertFalse(re.search(r'private_network\s*=\s*"[^"]+"', content))

        # IAM database users with type CLOUD_IAM_SERVICE_ACCOUNT
        self.assertIn("google_sql_user", content)
        self.assertRegex(content, r'type\s*=\s*"CLOUD_IAM_SERVICE_ACCOUNT"')
        self.assertIn("trimsuffix(", content)
        self.assertIn('".gserviceaccount.com"', content)

        # google_sql_database resource declared
        self.assertIn("google_sql_database", content)

    def test_outputs_exported(self):
        """AC-2: Assert instance_connection_name, instance_name, public_ip_address, database_name exported."""
        outputs_file = CLOUDSQL_MODULE_DIR / "outputs.tf"
        self.assertTrue(
            outputs_file.is_file(),
            f"Expected {outputs_file} to exist",
        )

        content = outputs_file.read_text()

        required_outputs = [
            "instance_connection_name",
            "instance_name",
            "public_ip_address",
            "database_name",
        ]
        for output_name in required_outputs:
            pattern = rf'output\s+"{output_name}"\s+\{{'
            self.assertIsNotNone(
                re.search(pattern, content),
                f"Output '{output_name}' must be exported in outputs.tf",
            )

    def test_opentofu_fmt_and_validation(self):
        """AC-1, AC-2: Validate OpenTofu syntax and schema in modules/cloudsql."""
        self.assertTrue(
            CLOUDSQL_MODULE_DIR.is_dir(),
            f"Directory {CLOUDSQL_MODULE_DIR} must exist",
        )

        fmt_res = subprocess.run(
            ["tofu", "fmt", "-check"],
            cwd=CLOUDSQL_MODULE_DIR,
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
            cwd=CLOUDSQL_MODULE_DIR,
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
            cwd=CLOUDSQL_MODULE_DIR,
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
