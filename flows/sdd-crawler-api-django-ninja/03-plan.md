# Plan: Crawler API Migration to Django Ninja

**Version:** 1.0
**Status:** DRAFT
**Last Updated:** 2026-04-19

---

## 1. Task Breakdown

### Phase 1: Foundation (3 tasks)
- [ ] **Task 1.1: Update dependencies.** Add `django` and `django-ninja` to `requirements.txt`.
- [ ] **Task 1.2: Initialize Django structure.** Create `crawler/api/ninja/` with `app.py`, `urls.py`, and `settings.py` (minimal).
- [ ] **Task 1.3: Request Enrichment Middleware.** Implement middleware to attach `lpm`, `config_loader`, etc., to the request.

### Phase 2: Read-Only Routers (3 tasks)
- [ ] **Task 2.1: Health Router.** Port `GET /health` with queue stats and LPM status.
- [ ] **Task 2.2: Metrics Router.** Port `GET /metrics` for Prometheus.
- [ ] **Task 2.3: Config Router.** Port `GET /config` and `GET /config/{platform}`.

### Phase 3: Task & Data Routers (3 tasks)
- [ ] **Task 3.1: Tasks Router.** Port CRUD and retry operations for tasks.
- [ ] **Task 3.2: Scrape Router.** Port manual `/scrape` submission.
- [ ] **Task 3.3: Bulk Router.** Port `/bulk/import`.

### Phase 4: System & Maintenance (3 tasks)
- [ ] **Task 4.1: Logs Router.** Port `GET /logs` with SQLite backend.
- [ ] **Task 4.2: System Router.** Port `POST /restart` and `GET /status`.
- [ ] **Task 4.3: Webhooks Router.** Port `POST /webhooks`.

### Phase 5: Verification & Integration (2 tasks)
- [ ] **Task 5.1: Parallel Execution Test.** Allow both FastAPI and Ninja to run (different ports or paths) for verification.
- [ ] **Task 5.2: Final Switchover.** Update main entry point to use Django Ninja exclusively.

---

## 2. Dependencies

1.  **Task 1.2** depends on **Task 1.1**.
2.  **Task 1.3** depends on **Task 1.2**.
3.  All **Phase 2-4** tasks depend on **Task 1.3**.
4.  **Phase 5** depends on all previous tasks.

---

## 3. Complexity Estimates

- **Phase 1:** Low-Medium
- **Phase 2:** Low
- **Phase 3:** Medium
- **Phase 4:** Low
- **Phase 5:** Low

---

## 4. Acceptance Criteria

- All existing FastAPI endpoints must have a functional equivalent in Django Ninja.
- Request/Response JSON structure must remain identical.
- Swagger documentation must be accessible at `/api/docs` (default Ninja path).
- The crawler must still be able to run and be managed via the new API.

---

## 5. Next Steps
1.  Submit plan for approval.
2.  Start Phase 1.
