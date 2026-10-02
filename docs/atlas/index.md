---
okf_version: '0.2'
generated_at_commit: 97f26a8d748c0207987adcc1ae4ff1a50e76dd4e
---
# Infrastructure Documentation

Welcome to the `sample-infra` documentation. This wiki covers the cloud architecture, serverless compute runtimes, managed persistence, security boundaries, and automated deployment pipelines for the sample application stack.

## Subsystems and Concepts

- [Infrastructure Overview](overview.md) — Scope, purpose, and role of the infrastructure repository within the sample application ecosystem.
- [Cloud Infrastructure Architecture](architecture.md) — Architectural blueprint and topology connecting frontend, backend, relational database, object storage, and secrets management.
- [Container Runtimes and Compute Services](compute.md) — Serverless container compute specifications on Google Cloud Run for backend API and frontend static delivery services.
- [Relational Database Infrastructure](database.md) — Managed Cloud SQL PostgreSQL provisioning, IAM database authentication, automated backups, and private network integration.
- [Object Storage and Asset Management](storage.md) — Google Cloud Storage bucket configuration, CORS rules for browser uploads, path partitioning, and access policies.
- [IAM, Secrets, and Security Architecture](security.md) — Principle of least privilege, service account roles, Secret Manager secrets injection, and security boundary enforcement.
- [Networking and Traffic Management](networking.md) — Ingress routing, TLS certificate management, Serverless VPC Access, and private network integration.
- [CI/CD and Deployment Workflows](deployment.md) — Continuous integration, multi-stage image builds, environment promotion, and Cloud Run revision rollouts.
