---
okf_version: '0.2'
generated_at_commit: e5c6a19239452f1300d6e04a074147cdda4e64b0
---
# Infrastructure Documentation

Welcome to the `sample-infra` documentation. This wiki covers the cloud architecture, OpenTofu modules, serverless compute runtimes, managed persistence, security boundaries, and environment deployment workflows for the sample application stack.

## Subsystems and Concepts

- [Infrastructure Overview](overview.md) — Scope, module composition, and environment orchestration for the sample application stack.
- [Cloud Infrastructure Architecture](architecture.md) — Architectural blueprint and module integration connecting frontend, backend, relational database, object storage, and secrets management.
- [Container Runtimes and Compute Services](compute.md) — Serverless Cloud Run v2 services and database migration jobs provisioned via OpenTofu.
- [Relational Database Infrastructure](database.md) — Managed Cloud SQL PostgreSQL provisioning with IAM database authentication and zero static passwords.
- [Object Storage and Asset Management](storage.md) — Google Cloud Storage bucket configuration with Uniform Bucket-Level Access and CORS for direct client uploads.
- [IAM, Secrets, and Security Architecture](security.md) — Least-privilege IAM service accounts, passwordless database authentication, and Secret Manager integration.
- [Networking and Traffic Management](networking.md) — Ingress routing, public IPv4 Cloud SQL connectivity with mTLS, and cross-origin resource sharing.
- [CI/CD and Deployment Workflows](deployment.md) — Declarative OpenTofu environment orchestration, API provisioning, migration job execution, and test validation.
