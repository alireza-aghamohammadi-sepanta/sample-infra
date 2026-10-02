---
type: concept
title: CI/CD and Deployment Workflows
summary: Continuous integration, multi-stage image builds, environment promotion, and Cloud Run revision rollouts.
related: ["overview.md", "architecture.md", "compute.md"]
source_paths: []
---

# CI/CD and Deployment Workflows

The deployment workflow standardizes build, validation, database migration, and rollout procedures across all environments. It coordinates artifact generation from application repositories (`sample-backend` and `sample-frontend`) with infrastructure state managed in `sample-infra`.

## Continuous Deployment Pipeline

```
+--------------------+        +--------------------+        +--------------------+
|  1. Code Commit    | -----> |  2. Build & Test   | -----> | 3. Publish Image   |
|  - PR Merge to dev |        |  - Pytest / Vitest |        |  - Google Artifact |
|    or main branch  |        |  - Multi-stage OCI |        |    Registry (GAR)  |
+--------------------+        +--------------------+        +---------+----------+
                                                                      |
                                                                      v
+--------------------+        +--------------------+        +--------------------+
| 6. Complete        | <----- | 5. Deploy Revision | <----- | 4. Run Migrations  |
|  - 100% Traffic    |        |  - Cloud Run Apply |        |  - Cloud Run Job   |
|  - Old Rev Scaled  |        |  - Canary / Health |        |  - Alembic Head    |
+--------------------+        +--------------------+        +--------------------+
```

### Pipeline Stages

1. **Continuous Integration & Testing:**
   - Every commit triggers automated linters, type checks (`tsc`, `mypy`), and test suites (`vitest`, `pytest`).
2. **Container Artifact Generation:**
   - The backend uses a multi-stage Docker build with Astral `uv` to produce an image based on Python 3.13-bookworm-slim.
   - The frontend compiles TypeScript and React into static distribution files and packages them into an unprivileged Nginx image.
   - Images are tagged with git commit SHAs and pushed to Google Artifact Registry.
3. **Database Schema Migration:**
   - Prior to serving user traffic with new code, a Google Cloud Run Job invokes `alembic upgrade head`.
   - If migrations fail, the deployment halts, preventing application crashes due to schema mismatch.
4. **Cloud Run Revision Rollout:**
   - Cloud Run provisions a new immutable revision using the freshly published container image.
   - Startup probes verify container readiness before traffic is shifted.
5. **Traffic Allocation & Rollback:**
   - By default, traffic shifts to 100% upon successful startup.
   - For major releases, canary traffic splitting (e.g. 10% to new revision, 90% to stable revision) validates performance in production.
   - If errors occur, rolling back is instant by reallocating 100% traffic to the preceding healthy revision.

## Environment Segregation

The infrastructure architecture supports three isolated environments:

| Environment | Purpose | Database Configuration | Compute Scaling |
| :--- | :--- | :--- | :--- |
| **Development (`dev`)** | Feature development and continuous testing | Single-zone Cloud SQL, shared micro instance | Scale-to-zero (`min_instances = 0`) |
| **Staging (`stage`)** | Pre-production validation and integration | Single-zone Cloud SQL with production-like schema | Scale-to-zero with scheduled warm-up |
| **Production (`prod`)** | Live end-user traffic | Multi-zone Cloud SQL High Availability with PITR | Dedicated warm instance (`min_instances = 1+`) |

## Infrastructure as Code (IaC) Management

Infrastructure resources (VPC, Cloud SQL, Cloud Storage buckets, Secret Manager secrets, and IAM service accounts) are maintained declaratively:
- **State Storage:** Remote state stored in a dedicated Google Cloud Storage bucket with object versioning and state locking.
- **Auditability:** All infrastructure changes are peer-reviewed via pull requests, and automated speculative plans are executed before applying changes.
