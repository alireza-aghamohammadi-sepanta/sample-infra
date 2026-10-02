---
type: concept
title: Networking and Traffic Management
summary: Ingress routing, TLS certificate management, Serverless VPC Access, and private network integration.
related: ["architecture.md", "compute.md", "security.md"]
source_paths: []
---

# Networking and Traffic Management

The networking architecture manages traffic ingress from public clients, internal communication between serverless containers and private relational databases, and secure egress to Google Cloud storage endpoints.

## Ingress & Edge Routing

All external client traffic enters Google Cloud through Google's global edge network:

```
+--------------------------------------------------------------------------------+
|                             Google Edge Network                                |
|  - Managed TLS Termination (TLS 1.3 / HTTP/2)                                  |
|  - Anycast Global IPs / DNS Anycast Routing                                    |
+---------------------------------------+----------------------------------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
                 v                                             v
+---------------------------------+           +----------------------------------+
| Frontend Ingress (Cloud Run)    |           | Backend Ingress (Cloud Run)      |
| https://app.example.com         |           | https://api.example.com          |
| (or https://frontend-*.run.app) |           | (or https://backend-*.run.app)   |
+---------------------------------+           +----------------------------------+
```

### Ingress Features
- **Automated TLS Certificates:** Google-managed SSL/TLS certificates handle automatic provisioning and renewal without manual certificate management.
- **Custom Domains:** Supports direct Cloud Run domain mappings or upstream integration with a Google Cloud External HTTP(S) Load Balancer for multi-region routing, Cloud CDN caching, and Cloud Armor DDoS protection.
- **Protocol Support:** Native support for HTTP/2, WebSockets, and standard HTTP/1.1 streaming.

## Serverless VPC Access & Private Networking

To isolate the relational database from public internet exposure, Cloud SQL is deployed with a Private IP address within a Virtual Private Cloud (VPC) network. Cloud Run connects to this private network using a **Serverless VPC Access Connector**:

```
+-----------------------------------+
| Cloud Run Container               |
| (sample-backend)                  |
+-----------------+-----------------+
                  |
                  | Serverless VPC Connector
                  v
+--------------------------------------------------------------------------------+
| Custom VPC Network (Default Subnet: 10.0.0.0/24)                               |
|                                                                                |
|  +------------------------------+       +------------------------------------+ |
|  | Serverless VPC Connector     | ----> | Private Service Connect / PSA      | |
|  | (e.g. 10.8.0.0/28)           |       | (Allocated IP Range: 10.128.0.0/16)| |
|  +------------------------------+       +-----------------+------------------+ |
|                                                           |                    |
|                                                           v                    |
|                                         +------------------------------------+ |
|                                         | Cloud SQL PostgreSQL Instance      | |
|                                         | (Private IP: 10.128.0.3)           | |
|                                         +------------------------------------+ |
+--------------------------------------------------------------------------------+
```

### Routing Rules
- **Private Egress Only:** Cloud Run route settings route traffic destined for private RFC 1918 ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`) across the VPC connector.
- **Public Egress:** Outbound requests to external APIs, SMTP mail relays, or public Google APIs (such as Cloud Storage and Secret Manager) travel through Google's default internet gateway.

## Cross-Origin Resource Policy (CORS)

Communication between the frontend SPA (origin: `https://app.example.com`) and backend API (origin: `https://api.example.com`):
- The FastAPI application configures `CORSMiddleware` with allowed origins matching the frontend domains.
- Allowed HTTP methods include `GET`, `POST`, `PUT`, `DELETE`, `OPTIONS`.
- Allowed headers include `Authorization`, `Content-Type`, and standard tracking headers.
