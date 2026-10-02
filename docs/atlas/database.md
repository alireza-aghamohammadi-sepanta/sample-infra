---
type: concept
title: Relational Database Infrastructure
summary: Managed Cloud SQL PostgreSQL provisioning, IAM database authentication, automated backups, and private network integration.
related: ["architecture.md", "compute.md", "security.md"]
source_paths: []
---

# Relational Database Infrastructure

The relational persistence tier is powered by **Google Cloud SQL for PostgreSQL**. It houses relational entities such as user accounts, authentication tokens, todo items, and asset metadata. The database architecture emphasizes automated failover, data durability, and passwordless IAM-mediated access controls.

## Engine & Instance Specifications

- **Database Engine:** PostgreSQL 16
- **Storage Type:** SSD (Solid State Drive) persistent storage with automatic capacity expansion enabled.
- **High Availability (HA):**
  - *Production:* Regional high-availability deployment with automatic failover across multiple availability zones within the chosen Google Cloud region.
  - *Development / Staging:* Single-zone configuration to minimize resource costs.
- **Connection Flags:** Optimized connection parameters, timezone setting (`UTC`), and SSL enforcement (`sslmode=require`).

## Connection Architecture & IAM Authentication

To eliminate the risks associated with static credentials and rotated passwords, the infrastructure leverages **Cloud SQL IAM Database Authentication**:

```
+-----------------------------------+             +----------------------------------+
| Backend Service Account           |             | Google Cloud SQL Instance        |
| (sample-backend@proj.iam.gservice)|             | (PostgreSQL 16)                  |
+-----------------+-----------------+             +-----------------+----------------+
                  |                                                 ^
                  | 1. Request Ephemeral Connect Certificate        |
                  v                                                 |
+-----------------------------------+                               |
| Cloud SQL Admin API               |                               |
+-----------------+-----------------+                               |
                  |                                                 |
                  | 2. Validated IAM Identity & Short-lived Cert    |
                  v                                                 |
+-----------------------------------+                               |
| Cloud SQL Python Connector        +-------------------------------+
| (mTLS Tunnel & IAM DB User Auth)  |  3. Encrypted Database Session
+-----------------------------------+
```

### Advantages of IAM Database Auth
- **Zero Static Passwords:** The backend service account authenticates using short-lived credentials generated dynamically by the Cloud SQL Admin API.
- **Built-in Mutual TLS:** All connections established through the Cloud SQL Python Connector or Cloud SQL Auth Proxy are encrypted end-to-end via ephemeral SSL certificates.
- **Granular Access Revocation:** Database access is governed centrally via GCP IAM roles (`roles/cloudsql.client` and `roles/cloudsql.instanceUser`).

## Backup & Recovery Architecture

Data durability and disaster recovery SLAs are maintained through:
- **Automated Daily Backups:** Point-in-time snapshots captured during off-peak operational windows with a minimum retention period of 7 days (30 days for production).
- **Point-in-Time Recovery (PITR):** Write-Ahead Logging (WAL) archiving enabled, permitting granular restoration of database state to any specific second within the retention window.
- **Storage Auto-Resize:** Dynamically expands storage volume before capacity reaches 80% utilization, preventing database write freezes caused by full disks.

## Database Migrations Pipeline

Schema changes are managed through Alembic migration scripts defined in the backend repository. In cloud environments:
1. Migrations are executed as isolated **Google Cloud Run Jobs** prior to deploying new application revisions.
2. The migration job runs with elevated schema-migration database privileges.
3. Once the migration job reports zero exit status, traffic is migrated to the new backend service revision.
