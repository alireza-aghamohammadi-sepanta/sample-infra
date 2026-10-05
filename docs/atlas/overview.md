---
type: concept
title: Infrastructure Overview
summary: Overview of the infrastructure repository, OpenTofu modules, and environment orchestration for the sample application stack.
related: ["architecture.md", "compute.md", "database.md", "storage.md", "security.md", "networking.md", "deployment.md"]
source_paths: ["environments/dev/main.tf", "environments/dev/variables.tf", "environments/dev/outputs.tf"]
---

# Infrastructure Overview

`sample-infra` serves as the centralized infrastructure repository for the Sepanta sample application ecosystem. It defines, manages, and orchestrates the cloud resources and deployment specifications required to run the full application stack, comprising the asynchronous FastAPI REST backend (`sample-backend`) and the React 18 / TypeScript single-page frontend (`sample-frontend`).

## Repository Architecture & Structure

The repository organizes cloud resources declaratively using OpenTofu / Terraform:

```
sample-infra/
├── environments/
│   └── dev/                    # Development environment orchestration
│       ├── backend.tf.example  # GCS remote state configuration template
│       ├── main.tf             # API enablement, module wiring, and secrets
│       ├── outputs.tf          # Service URLs, connection names, and migration commands
│       ├── terraform.tfvars.example # Sample variable inputs
│       ├── variables.tf        # Environment input variable declarations
│       └── versions.tf         # OpenTofu and Google provider version constraints
├── modules/
│   ├── cloudrun/               # Cloud Run v2 services (backend, frontend) and migration job
│   ├── cloudsql/               # Managed Cloud SQL PostgreSQL instance and IAM DB users
│   ├── iam/                    # Workload service accounts and least-privilege role bindings
│   └── storage/                # Cloud Storage asset bucket with UBLA and CORS rules
├── tests/                      # Python module and environment validation test suites
└── docs/atlas/                 # Repository architecture and subsystem wiki
```

## System Architecture

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
                     |                   | API Calls (JSON)  |
                     |                   v                   |
                     |  +---------------------------------+  |
                     |  |  Google Cloud Run (Backend)     |  |
                     |  |  - FastAPI (Port 8000)          |  |
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

1. [Compute and Container Runtimes](compute.md): Serverless container hosting on Google Cloud Run for both the backend API and frontend static web server, plus Cloud Run Jobs for database schema migrations.
2. [Target Architecture](architecture.md): Topology, interaction patterns, and operational boundaries linking compute, storage, and networking layers.
3. [Relational Database](database.md): Managed PostgreSQL 16 database on Google Cloud SQL featuring passwordless IAM database authentication and automated SSD auto-resizing.
4. [Object Storage](storage.md): Google Cloud Storage (GCS) buckets equipped with Uniform Bucket-Level Access and cross-origin resource sharing (CORS) rules for direct pre-signed URL uploads.
5. [Security & Identity](security.md): Identity and Access Management (IAM) service accounts, least-privilege role bindings, and Google Cloud Secret Manager for runtime credential management (`JWT_SECRET`, `DATABASE_INSTANCE`).
6. [Networking & Traffic](networking.md): HTTPS ingress termination, Cloud SQL direct connection with mTLS and Cloud SQL Connector, and cross-origin resource policies.
7. [Deployment & CI/CD](deployment.md): Declarative OpenTofu module composition, GCP API activation, automated test suites (`.tftest.hcl` and `pytest`), and database migration commands.
