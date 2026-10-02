---
type: concept
title: Infrastructure Overview
summary: Overview of the infrastructure repository, operational scope, and deployment target for the sample application stack.
related: ["architecture.md", "compute.md", "database.md", "storage.md", "security.md", "networking.md", "deployment.md"]
source_paths: []
---

# Infrastructure Overview

`sample-infra` serves as the centralized infrastructure repository for the Sepanta sample application ecosystem. It defines, manages, and orchestrates the cloud resources and deployment specifications required to run the full application stack, comprising the asynchronous FastAPI REST backend (`sample-backend`) and the React 18 / TypeScript single-page frontend (`sample-frontend`).

## Ecosystem Role

The repository encapsulates infrastructure-as-code (IaC) blueprints, environment configurations, and deployment pipelines. Rather than embedding cloud provisioning logic inside application service repositories, `sample-infra` isolates cloud infrastructure concerns into a dedicated operational boundary.

```
                     +---------------------------------------+
                     |             Client Browser            |
                     +-------------------+-------------------+
                                         |
                       HTTPS Requests    |   Signed URL Direct Uploads
                                         v
                     +---------------------------------------+
                     |         sample-infra (GCP)            |
                     |                                       |
                     |  +---------------------------------+  |
                     |  |  Google Cloud Run (Frontend)    |  |
                     |  |  - Nginx unprivileged (Port 8080)  |
                     |  +---------------------------------+  |
                     |                   |                   |
                     |                   | API Calls         |
                     |                   v                   |
                     |  +---------------------------------+  |
                     |  |  Google Cloud Run (Backend)     |  |
                     |  |  - FastAPI / Python 3.13        |  |
                     |  +--------+---------------+--------+  |
                     |           |               |           |
                     |      IAM  |          gcs  |  v4 URLs  |
                     |      Auth v               v           |
                     |  +--------------+  +---------------+  |
                     |  |  Cloud SQL   |  | Cloud Storage |  |
                     |  | (PostgreSQL) |  |   (Assets)    |  |
                     |  +--------------+  +---------------+  |
                     |           |                           |
                     |           v                           |
                     |  +------------------------------+     |
                     |  |    Secret Manager & IAM      |     |
                     |  +------------------------------+     |
                     +---------------------------------------+
```

## Core Cloud Subsystems

The infrastructure targets Google Cloud Platform (GCP) and leverages managed, serverless, and cloud-native services:

1. [Compute and Container Runtimes](compute.md): Serverless container hosting on Google Cloud Run for both the backend API and frontend static web server.
2. [Target Architecture](architecture.md): Topology, interaction patterns, and operational boundaries linking compute, storage, and networking layers.
3. [Relational Database](database.md): Managed PostgreSQL database on Google Cloud SQL featuring IAM authentication and connection pooling via the Cloud SQL Python Connector.
4. [Object Storage](storage.md): Google Cloud Storage (GCS) buckets equipped with cross-origin resource sharing (CORS) rules for direct pre-signed URL uploads.
5. [Security & Identity](security.md): Identity and Access Management (IAM) service accounts, least-privilege role binding, and Google Cloud Secret Manager for runtime credential injection.
6. [Networking & Traffic](networking.md): HTTPS ingress termination, Serverless VPC Access connectors for private database access, and cross-origin resource policies.
7. [Deployment & CI/CD](deployment.md): Multi-stage container builds, environment separation (`dev`, `staging`, `production`), and deployment orchestration.

## Repository State

The repository is structured to hold infrastructure manifests, Terraform or OpenTofu modules, and CI/CD pipelines. As an infrastructure repository, it decouples cloud resource provisioning from application code release cadences, ensuring reliable, reproducible, and auditable cloud environments.
