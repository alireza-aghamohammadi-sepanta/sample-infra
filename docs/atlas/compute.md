---
type: concept
title: Container Runtimes and Compute Services
summary: Serverless container compute specifications on Google Cloud Run for backend API and frontend static delivery services.
related: ["architecture.md", "networking.md", "security.md", "deployment.md"]
source_paths: []
---

# Container Runtimes and Compute Services

The compute tier relies on **Google Cloud Run**, a managed serverless platform that runs stateless containers directly on top of Google Cloud's infrastructure. It provides automatic horizontal scaling, scale-to-zero capabilities, request-based autoscaling, and managed TLS termination.

## Service Specifications

The system defines two primary Cloud Run services corresponding to the frontend and backend microservices:

| Parameter | Frontend Service (`sample-frontend`) | Backend Service (`sample-backend`) |
| :--- | :--- | :--- |
| **Container Image** | Built from `nginxinc/nginx-unprivileged:alpine` | Built from `ghcr.io/astral-sh/uv:python3.13-bookworm-slim` |
| **Listening Port** | `8080` (Nginx unprivileged standard) | `8080` / `8000` (FastAPI / Uvicorn standard) |
| **CPU Allocation** | 1 vCPU | 1 to 2 vCPU |
| **Memory Allocation** | 256 MiB | 512 MiB to 1 GiB |
| **Concurrency** | Up to 1000 concurrent requests | 80 concurrent requests per container instance |
| **Min Instances** | 0 (Scale-to-zero for dev/staging) / 1 (Prod) | 0 (Dev) / 1 (Prod to mitigate cold starts) |
| **Max Instances** | 10 to 50 | 20 to 100 |
| **Execution Environment** | Second generation (standard) | Second generation (supports Unix sockets & gVisor) |
| **Service Identity** | Frontend runtime service account | Backend API service account with IAM bindings |

## Backend Runtime Profile

The backend service runs a FastAPI application packaged using Astral `uv`:

```
+-------------------------------------------------------------+
| Cloud Run Container Instance: sample-backend                |
|                                                             |
|  +-------------------------------------------------------+  |
|  | Entrypoint: uvicorn main:app --host 0.0.0.0 --port 8080 |  |
|  +-------------------------------------------------------+  |
|                             |                               |
|        +--------------------+--------------------+          |
|        |                                         |          |
|        v                                         v          |
|  +---------------------------+       +-------------------+  |
|  | Cloud SQL Python Connector|       | GCS Storage Client|  |
|  | - IAM Authentication      |       | - V4 Presigned URL|  |
|  | - Unix Socket / Loopback  |       +-------------------+  |
|  +---------------------------+                              |
+-------------------------------------------------------------+
```

### Key Runtime Behaviors
- **Connection Handling:** Database connectivity is initialized lazily during application lifespan via the Cloud SQL Python Connector or direct async connection pool.
- **Resource Constraints:** Non-blocking asynchronous I/O allows a single container to process high volumes of concurrent HTTP requests without thread starvation.
- **Health Checks:** Cloud Run monitors HTTP startup probes and liveness probes at the root or `/docs` endpoint to ensure container readiness prior to routing incoming traffic.

## Frontend Runtime Profile

The frontend service serves the pre-compiled Vite React SPA:
- **Web Server:** Unprivileged Nginx listening on port 8080.
- **SPA Routing:** Configured with fallback rewrite rules (`try_files $uri $uri/ /index.html`) to support client-side HTML5 history routing without 404 errors.
- **Static Asset Optimization:** In-memory gzip compression enabled for JavaScript, CSS, and SVG payloads.
- **Caching Headers:** Immutable cache headers for fingerprinted assets in `/assets/` and short-lived or no-cache headers for `index.html`.

## Autoscaling & Revision Management

- **Scale to Zero:** Cloud Run automatically scales instances to zero during idle periods to reduce operational expenditure.
- **Cold-Start Mitigation:** For production tiers, `min_instances = 1` can be designated on the backend service to guarantee instantaneous response times for interactive user requests.
- **Blue-Green Deployments:** Each container image deployment creates a unique, immutable Cloud Run revision. Traffic can be migrated instantly or split proportionally (canary release) using native Cloud Run traffic allocation rules.
