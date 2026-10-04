"""Module validation tests for Storage module.

Covers: AC-1, AC-2
- Asserts modules/storage requires bucket_name and region (no default values).
- Asserts location, storage_class, and CORS origins variables are defined.
- Asserts uniform_bucket_level_access is set to true.
- Asserts public_access_prevention is set to "enforced".
- Asserts CORS rules specify GET, PUT, OPTIONS with 3600 max age.
- Asserts outputs bucket_name and bucket_url are exported.
- Validates OpenTofu fmt, init, and validate.
"""

import os
import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
STORAGE_MODULE_DIR = REPO_ROOT / "modules" / "storage"


class TestStorageModuleValidation(unittest.TestCase):
    def test_variables_declared_and_required(self):
        """AC-1, AC-2: Assert required inputs bucket_name and region have no defaults, and storage variables exist."""
        variables_file = STORAGE_MODULE_DIR / "variables.tf"
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
            "bucket_name",
            "region",
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

        # Assert location is defined as an input
        self.assertIn(
            "location",
            vars_dict,
            "Variable 'location' must be declared in variables.tf",
        )

        # Assert storage_class is defined and defaults to STANDARD
        self.assertIn(
            "storage_class",
            vars_dict,
            "Variable 'storage_class' must be declared in variables.tf",
        )
        self.assertIn(
            "STANDARD",
            vars_dict["storage_class"],
            "Variable 'storage_class' must default to 'STANDARD'",
        )

        # Assert allowed CORS origins input variable is defined
        self.assertTrue(
            "cors_origins" in vars_dict or "allowed_origins" in vars_dict,
            "CORS origins variable must be declared in variables.tf",
        )

    def test_bucket_security_and_cors_declared(self):
        """AC-1, AC-2: Assert uniform bucket level access, public access prevention, and CORS rules."""
        main_file = STORAGE_MODULE_DIR / "main.tf"
        self.assertTrue(
            main_file.is_file(),
            f"Expected {main_file} to exist",
        )

        content = main_file.read_text()

        # google_storage_bucket resource declared
        self.assertIn(
            "google_storage_bucket",
            content,
            "main.tf must declare google_storage_bucket",
        )

        # Uniform bucket-level access enforced
        self.assertRegex(
            content,
            r'uniform_bucket_level_access\s*=\s*true',
            "uniform_bucket_level_access must be set to true",
        )

        # Public access prevention enforced
        self.assertRegex(
            content,
            r'public_access_prevention\s*=\s*"enforced"',
            'public_access_prevention must be set to "enforced"',
        )

        # CORS block exists
        self.assertIn("cors", content, "main.tf must declare cors block")

        # CORS methods GET, PUT, OPTIONS
        self.assertIn('"GET"', content, 'CORS rules must specify "GET"')
        self.assertIn('"PUT"', content, 'CORS rules must specify "PUT"')
        self.assertIn('"OPTIONS"', content, 'CORS rules must specify "OPTIONS"')

        # CORS max age 3600
        self.assertRegex(
            content,
            r'max_age_seconds\s*=\s*3600',
            "CORS max_age_seconds must be 3600",
        )

        # Response headers Content-Type, Content-Length, ETag, x-goog-*
        self.assertIn('"Content-Type"', content)
        self.assertIn('"Content-Length"', content)
        self.assertIn('"ETag"', content)
        self.assertIn('"x-goog-*"', content)

    def test_outputs_exported(self):
        """AC-2: Assert bucket_name and bucket_url are exported in outputs.tf."""
        outputs_file = STORAGE_MODULE_DIR / "outputs.tf"
        self.assertTrue(
            outputs_file.is_file(),
            f"Expected {outputs_file} to exist",
        )

        content = outputs_file.read_text()

        required_outputs = [
            "bucket_name",
            "bucket_url",
        ]
        for output_name in required_outputs:
            pattern = rf'output\s+"{output_name}"\s+\{{'
            self.assertIsNotNone(
                re.search(pattern, content),
                f"Output '{output_name}' must be exported in outputs.tf",
            )

    def test_opentofu_fmt_and_validation(self):
        """AC-1, AC-2: Validate OpenTofu syntax and schema in modules/storage."""
        self.assertTrue(
            STORAGE_MODULE_DIR.is_dir(),
            f"Directory {STORAGE_MODULE_DIR} must exist",
        )

        fmt_res = subprocess.run(
            ["tofu", "fmt", "-check"],
            cwd=STORAGE_MODULE_DIR,
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
            cwd=STORAGE_MODULE_DIR,
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
            cwd=STORAGE_MODULE_DIR,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            val_res.returncode,
            0,
            f"tofu validate failed:\n{val_res.stdout}\n{val_res.stderr}",
        )

        test_res = subprocess.run(
            ["tofu", "test"],
            cwd=STORAGE_MODULE_DIR,
            capture_output=True,
            text=True,
        )
        self.assertEqual(
            test_res.returncode,
            0,
            f"tofu test failed:\n{test_res.stdout}\n{test_res.stderr}",
        )


if __name__ == "__main__":
    unittest.main()
