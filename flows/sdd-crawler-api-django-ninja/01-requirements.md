# Requirements: Crawler API Migration to Django Ninja

**Version:** 1.0
**Status:** DRAFT
**Last Updated:** 2026-04-19

---

## 1. Problem Statement

The crawler currently uses a FastAPI/Starlette-based API (see `crawler/api/`). While functional, the project architecture is moving towards **Django Ninja** for better integration with the broader ecosystem, standardized schema management, and to leverage Django's ORM/Admin if needed in the future.

## 2. Goal

Migrate the existing Crawler API endpoints from FastAPI/Starlette to **Django Ninja**.

---

## 3. Analysis of Existing Endpoints

Based on current SDDs (`sdd-crawler-ondemand`, `sdd-crawler-appsmith`) and `crawler/api/routes/`:

### 3.1. Crawler Management API (Local Control)
- **GET /health**: System health status, queue depth, uptime.
- **GET /config**: Current crawler configuration (platform, rate limits, etc.).
- **PUT /config**: Update crawler configuration.
- **GET /logs**: Fetch recent logs from SQLite/LPM.
- **POST /restart**: Graceful restart of workers/beat.
- **GET /metrics**: Prometheus metrics scraping.

### 3.2. Task Operations
- **POST /scrape**: Manual/on-demand task submission.
- **GET /tasks**: List tasks (from LPM/standalone_tasks).
- **GET /tasks/{id}**: Get details of a specific task.
- **POST /bulk/import**: Import tasks from local files (CSV/JSON).

### 3.3. Webhooks & Sync (External/Internal)
- **POST /webhooks**: Receive notifications (e.g., from Gateway).
- **GET /internal/work**: (Called by crawler to Gateway - client side).
- **POST /internal/results**: (Called by crawler to Gateway - client side).

## 4. Migration Requirements

### FR-1: Port All Existing Endpoints
- Every endpoint in `crawler/api/routes/*.py` must have a corresponding Django Ninja router/endpoint.
- Maintain identical request/response schemas to ensure compatibility with existing clients (e.g., AppSmith or monitoring scripts).

### FR-2: Schema Definition
- Use Pydantic models (Django Ninja's `Schema`) for all request/response validation.
- Standardize error responses (404 Not Found, 400 Bad Request, etc.).

### FR-3: Security & Middleware
- Port existing middleware (CORS, Request ID, Logging).
- Implement appropriate authentication (e.g., API Key or Basic Auth as defined in `sdd-crawler-flower`).

### FR-4: Integration with LPM
- Ensure Django Ninja endpoints correctly interact with `LocalPersistenceManager` (LPM) and the SQLite database.

## 5. Non-Goals
- Changing the underlying logic of the scraper or worker.
- Adding major new features during migration (unless necessary for the framework transition).

---

## 6. User Stories

### US-1: Developer Experience
**As a** developer
**I want** to use Django Ninja's automatic Swagger/OpenAPI documentation
**So that** I can easily test and understand the API.

### US-2: Operational Control
**As a** crawler operator
**I want** to monitor and configure the crawler via a unified Django-based API
**So that** it aligns with other tools in the infrastructure.

---

## 7. Next Steps
1.  Verify the complete list of endpoints in `crawler/api/routes/`.
2.  Define the Django Ninja structure within the project.
3.  Draft the specification for the new API layout.
