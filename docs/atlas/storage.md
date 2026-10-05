---
type: concept
title: Object Storage and Asset Management
summary: Google Cloud Storage bucket configuration with Uniform Bucket-Level Access and CORS for direct client uploads.
related: ["architecture.md", "compute.md", "security.md"]
source_paths: ["modules/storage/main.tf", "modules/storage/variables.tf", "modules/storage/outputs.tf", "modules/storage/tests/storage_validation.tftest.hcl", "tests/test_storage_module.py"]
---

# Object Storage and Asset Management

Object storage for uploaded assets, file attachments, and media is provisioned through `modules/storage`. The module configures a Google Cloud Storage (GCS) bucket optimized for secure direct client uploads via pre-signed V4 URLs while enforcing strict access policies.

## Bucket Configuration & Security Posture

The bucket resource (`google_storage_bucket.default`) enforces key security baselines:

- **Uniform Bucket-Level Access (UBLA):** Set to `uniform_bucket_level_access = true`. Disables legacy ACLs and unifies permissions under Google Cloud IAM.
- **Public Access Prevention:** Configured as `public_access_prevention = "enforced"`. Blocks any attempt to grant public read or write access via IAM policies or ACLs.
- **Location Resolution:** Defined dynamically via `coalesce(var.location, var.region)`, allowing callers to pass either variable.
- **Storage Class:** Defaults to `STANDARD`, configurable to `NEARLINE`, `COLDLINE`, or `ARCHIVE`.
- **Force Destroy:** Managed through `var.force_destroy` (set to `true` in development to facilitate clean environment tear downs).

## Cross-Origin Resource Sharing (CORS)

Web browser uploads directly to GCS via pre-signed URLs require explicit Cross-Origin Resource Sharing rules:

```terraform
cors {
  origin          = var.cors_origins
  method          = ["GET", "PUT", "OPTIONS"]
  response_header = ["Content-Type", "Content-Length", "ETag", "x-goog-*"]
  max_age_seconds = 3600
}
```

### Allowed Origins
Configured via `var.cors_origins` with defaults supporting local development and cloud hosting:
- `https://*.run.app` (Cloud Run domain routes)
- `https://sample-app.example.com` (Custom domain endpoint)
- `http://localhost:5173` (Vite local development server)

### Pre-Signed URL Upload Flow

```
+----------------+      1. POST /assets/upload-url         +-------------------+
|                | --------------------------------------> |                   |
|                |      2. V4 Signed PUT URL               |   FastAPI Backend |
|                | <-------------------------------------- |   (sa-backend)    |
|  SPA Frontend  |                                         +-------------------+
|  (Browser)     |      3. HTTP OPTIONS (Preflight)
|                | ----------------------------------------+
|                |      4. 200 OK + CORS Headers           |
|                | <---------------------------------------+
|                |                                         v
|                |      5. Direct HTTP PUT (Payload)  +------------------------+
|                | ---------------------------------> | Google Cloud Storage   |
|                |      6. 200 OK (Uploaded)          | (Asset Bucket)         |
|                | <--------------------------------- |                        |
+----------------+                                    +------------------------+
```

## Module Inputs & Outputs

### Input Variables
- `bucket_name` (string, required): Global name for the GCS bucket.
- `region` (string, required): GCP region for regional bucket placement.
- `location` (string, optional, default: `null`): Custom location override.
- `storage_class` (string, default: `"STANDARD"`): Storage tier.
- `cors_origins` (list(string)): List of origins permitted in CORS headers.
- `project_id` (string, optional, default: `null`): GCP project ID.
- `force_destroy` (bool, default: `false`): Enables recursive bucket deletion during destroy operations.

### Module Outputs
- `bucket_name`: The resolved name of the created bucket (`google_storage_bucket.default.name`).
- `bucket_url`: The base URL formatted as `gs://<bucket_name>` (`google_storage_bucket.default.url`).

## Validation & Testing

- **OpenTofu Test Suite** (`modules/storage/tests/storage_validation.tftest.hcl`): Mocks the provider and validates bucket name and URL output properties on planned resources.
- **Python Integration Tests** (`tests/test_storage_module.py`): Verifies required variables without defaults, confirms `uniform_bucket_level_access` and `public_access_prevention` settings, tests CORS configuration parameters, and runs `tofu fmt` and `tofu validate`.
