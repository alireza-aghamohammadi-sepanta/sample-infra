---
type: concept
title: Object Storage and Asset Management
summary: Google Cloud Storage bucket configuration, CORS rules for browser uploads, path partitioning, and access policies.
related: ["architecture.md", "compute.md", "security.md"]
source_paths: []
---

# Object Storage and Asset Management

User-uploaded files, task attachments, and media assets are stored in **Google Cloud Storage (GCS)**. To optimize performance and reduce backend compute load, the infrastructure enables direct browser-to-bucket uploads using pre-signed V4 URLs issued by the backend service.

## Bucket Configuration & Security

The asset storage bucket is provisioned with security controls aligned with Google Cloud security best practices:

- **Uniform Bucket-Level Access (UBLA):** Enforced across all environments. Object-level Access Control Lists (ACLs) are disabled, ensuring that access permissions are governed strictly through IAM policies at the bucket level.
- **Public Access Prevention:** Public read/write access is blocked (`enforcePublicAccessPrevention: true`). No object inside the bucket can be made publicly discoverable over the public internet without an authenticated identity or cryptographic signed URL.
- **Location & Storage Class:** Provisioned as Regional Standard storage in the same GCP region as Cloud Run and Cloud SQL (e.g. `europe-west1` or `us-central1`), minimizing cross-region egress latency and network transfer costs.

## Cross-Origin Resource Sharing (CORS)

Direct client uploads via the browser require explicit CORS configuration on the bucket. Without these rules, web browsers block pre-signed PUT requests under the Same-Origin Policy.

```
+----------------+      1. Request Upload URL      +-------------------+
|                | ------------------------------> |                   |
|                |      2. Return V4 Signed URL    |   FastAPI Backend |
|                | <------------------------------ |                   |
|                |                                 +-------------------+
|  SPA Frontend  |
|  (Browser)     |      3. HTTP OPTIONS (Preflight)
|                | ------------------------------------+
|                |      4. 200 OK + CORS Headers       |
|                | <-----------------------------------+
|                |                                     v
|                |      5. Direct HTTP PUT       +---------------------+
|                | ----------------------------> | Google Cloud Storage|
|                |      6. 200 OK (Uploaded)     | (Asset Bucket)      |
|                | <---------------------------- |                     |
+----------------+                               +---------------------+
```

### Bucket CORS Specification
The bucket policy applies the following JSON manifest:

```json
[
  {
    "origin": [
      "https://*.run.app",
      "https://sample-app.example.com",
      "http://localhost:5173"
    ],
    "method": ["GET", "PUT", "OPTIONS"],
    "responseHeader": [
      "Content-Type",
      "Content-Length",
      "ETag",
      "x-goog-*"
    ],
    "maxAgeSeconds": 3600
  }
]
```

## Storage Path Architecture

Objects within the bucket are partitioned hierarchically to enforce logical tenant isolation:

```
gs://<PROJECT_ID>-assets/
└── assets/
    └── {user_id}/
        └── {asset_id}
```

- **Prefix Isolation:** Every file key includes the unique `user_id` uuid of the authenticated owner.
- **Integrity Validation:** When the frontend finishes uploading, it notifies the backend API. The backend queries the GCS bucket to verify blob existence and byte size before persisting the asset record into Cloud SQL.

## Lifecycle Management

Storage lifecycle management policies are configured to clean up dangling and abandoned uploads:
- **Incomplete Upload Eviction:** Automatically deletes uncommitted multipart upload chunks older than 7 days.
- **Retention Rules:** Optional archival policies transitioning older assets (e.g., >365 days) to Coldline or Archive storage classes for cost efficiency.
