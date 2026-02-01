# 🚀 Multi-Tenant Authentication & RBAC System

A production-grade authentication and authorization framework designed for scalable SaaS applications. This system implements **Multi-Tenancy**, **Role-Based Access Control (RBAC)**, and **Audit Logging** using a security-first approach and Clean Architecture.



---

## 🛠️ Tech Stack

* **Framework:** [FastAPI](https://fastapi.tiangolo.com/) (Python 3.11+)
* **Database:** [PostgreSQL 16](https://www.postgresql.org/) & [Async SQLAlchemy 2.0](https://www.sqlalchemy.org/)
* **Caching:** [Redis 7](https://redis.io/) (OTP & Rate Limiting)
* **Security:** [PyJWT](https://pyjwt.readthedocs.io/) (RS256)
* **Ops:** Docker & Docker Compose

## ✨ Key Features

### 🔐 Authentication
* **Asymmetric Security:** JWT authentication using **RS256** (Private/Public key pairs).
* **Token Lifecycle:** Short-lived access tokens paired with long-lived refresh tokens.
* **Replay Protection:** Refresh token rotation to detect and invalidate compromised sessions.
* **MFA Ready:** Built-in support for **OTP-based login**.
* **Instant Revocation:** Global token invalidation upon user deactivation.

### 🏢 Multi-Tenancy
* **Strict Isolation:** Logical data separation ensuring zero cross-tenant leakage.
* **Hybrid User Models:** Supports both **Global Users** (Admins) and **Tenant-Scoped Users**.
* **State Enforcement:** Centralized middleware to check for active/inactive tenant status.

### 🧑‍⚖️ Authorization (RBAC)
* **Granular Permissions:** Permission-based access using slugs and **wildcard support** (e.g., `users:*`).
* **Dynamic Evaluation:** Permissions are evaluated at runtime rather than being stored statically inside a JWT.
* **Role Hierarchy:** Support for both System-wide roles and Tenant-specific roles.

### 📝 Audit Logging
* **Comprehensive Tracking:** Captures the *Actor, Tenant Context, Action, Resource, IP Address,* and *Payload Snapshot*.
* **Compliance Ready:** Designed for security reviews and forensic analysis.

---

## 🏗️ Architecture & Design

This project follows **Clean Architecture** principles to decouple business logic from external frameworks and delivery mechanisms.



### Project Structure
```text
app/
├── api/                # Route Handlers & Dependencies
│   ├── v1/             # Versioned API Endpoints (auth, users, tenants, etc.)
│   └── deps/           # FastAPI Dependencies (Auth, DB session, Tenant context)
├── domains/            # Pure Business Logic (Services & Logic)
│   ├── auth/
│   ├── users/
│   ├── tenants/
│   ├── roles/
│   └── audit/
├── infrastructure/     # External Concerns
│   ├── db/             # Models & Async Session Management
│   └── repositories/   # Data Access Patterns
├── security/           # JWT, Hashing, & Encryption Logic
├── core/               # Config, Constants, & Logging
└── main.py             # Application Entry Point
```

## ▶️ Running Locally

```bash
docker compose up --build
