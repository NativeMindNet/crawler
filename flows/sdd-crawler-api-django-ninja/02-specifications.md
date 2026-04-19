# Specifications: Crawler API Migration to Django Ninja

**Version:** 1.0
**Status:** DRAFT
**Last Updated:** 2026-04-19

---

## 1. Architectural Overview

The migration will replace the existing FastAPI/Starlette API with a Django Ninja implementation. The new API will be located in `crawler/api/ninja/` to avoid conflicts during transition.

### 1.1. Technology Stack
- **Framework:** Django (minimal setup)
- **API Engine:** Django Ninja
- **Validation:** Pydantic (built-in to Django Ninja)
- **Web Server:** Uvicorn (remains as is)

### 1.2. Directory Structure
```
crawler/api/ninja/
├── __init__.py
├── app.py             # Main NinjaAPI instance
├── urls.py            # Django URL patterns
├── routers/           # Sub-routers for different modules
│   ├── __init__.py
│   ├── health.py
│   ├── config.py
│   ├── tasks.py
│   ├── bulk.py
│   ├── logs.py
│   ├── metrics.py
│   ├── scrape.py
│   ├── system.py
│   └── webhooks.py
└── schemas.py         # Pydantic schemas (reused/refactored from existing)
```

---

## 2. Dependency Injection & State Management

FastAPI uses `request.app.state`. In Django Ninja, we will use:
1.  **Global App Settings**: For static configuration.
2.  **Middleware**: To attach `lpm`, `config_loader`, etc., to the request object.
3.  **Django Settings**: For project-wide configuration.

### 2.1. Request Enrichment Middleware
A middleware will be responsible for attaching the following to each request:
- `request.lpm`: Instance of `LocalPersistenceManager`
- `request.config_loader`: Instance of `ConfigLoader`
- `request.platform`: Current platform identifier

---

## 3. Router Mapping

| Current Route (FastAPI) | Ninja Router | Endpoints |
|-------------------------|--------------|-----------|
| `routes/health.py` | `routers/health.py` | `GET /health` |
| `routes/config.py` | `routers/config.py` | `GET /config`, `GET /config/{p}`, `POST /config/{p}/validate` |
| `routes/tasks.py` | `routers/tasks.py` | `GET /tasks`, `POST /tasks`, `GET /tasks/{id}`, `DELETE /tasks/{id}`, `POST /tasks/{id}/retry`, `POST /tasks/retry-bulk` |
| `routes/logs.py` | `routers/logs.py` | `GET /logs` |
| `routes/system.py` | `routers/system.py` | `POST /restart`, `GET /status` |
| `routes/scrape.py` | `routers/scrape.py` | `POST /scrape` |
| `routes/bulk.py` | `routers/bulk.py` | `POST /bulk/import` |
| `routes/metrics.py` | `routers/metrics.py` | `GET /metrics` |
| `routes/webhooks.py` | `routers/webhooks.py` | `POST /webhooks` |

---

## 4. API Schema Standardization

All response schemas will follow the existing Pydantic models from `crawler/api/schemas.py`. These will be moved/copied to `crawler/api/ninja/schemas.py`.

### 4.1. Error Handling
We will use Ninja's Exception Handlers to provide consistent JSON error responses:
```json
{
  "detail": "Error message",
  "code": "error_code"
}
```

---

## 5. Security

- **Basic Auth**: For administrative endpoints (`/config`, `/restart`, `/logs`).
- **API Key**: Optional for `/scrape` and `/bulk`.
- **CORS**: Re-implement standard CORS headers.

---

## 6. Implementation Strategy

1.  **Phase 1: Foundation**
    - Add `django` and `django-ninja` to `requirements.txt`.
    - Create `crawler/api/ninja/` structure.
    - Minimal `settings.py` for Django.
2.  **Phase 2: Core Routers**
    - Port `health`, `metrics`, and `config` (Read-only).
3.  **Phase 3: Task Management**
    - Port `tasks`, `scrape`, and `bulk`.
4.  **Phase 4: System & Logs**
    - Port `system`, `logs`, and `webhooks`.
5.  **Phase 5: Switchover**
    - Update `crawler/api/app.py` to optionally or fully point to Django Ninja.
    - Update `Dockerfile` and `docker-compose.yml` if necessary.

---

## 7. Next Steps
1.  Initialize Django Ninja project structure.
2.  Verify `lpm` and `config_loader` accessibility from Django context.
3.  Implement the first router (`health`).
