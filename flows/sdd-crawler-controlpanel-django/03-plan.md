# Plan: Crawler Control Panel (Django UI)

**Version:** 3.0
**Status:** DRAFT
**Last Updated:** 2026-04-19

---

## 1. Task Breakdown

### Phase 1: Foundation (2 tasks)
- [ ] **Task 1.1: Project Setup.** Initialize Django project in `crawler/controlpanel/` with minimal settings.
- [ ] **Task 1.2: Settings & DB.** Configure `DATABASES` to point to `lpm.db` and setup static files for Bootstrap 5.

### Phase 2: Model & Admin Mapping (2 tasks)
- [ ] **Task 2.1: Model Definitions.** Map existing SQLite tables to unmanaged Django models.
- [ ] **Task 2.2: Admin Customization.** Register models in `admin.py` with custom filters and search fields.

### Phase 3: Custom UI Implementation (2 tasks)
- [ ] **Task 3.1: Dashboard.** Create the main dashboard view with metrics and health summary.
- [ ] **Task 3.2: Log Viewer.** Implement the web interface for browsing and filtering logs from SQLite.

### Phase 4: Integration (2 tasks)
- [ ] **Task 4.1: Action Hooks.** Implement UI triggers for crawler-related actions (e.g., re-queue, restart).
- [ ] **Task 4.2: Deployment Config.** Update `docker-compose.yml` to include the Control Panel service.

---

## 2. Dependencies
- Phase 2 depends on Phase 1.
- Phase 3 depends on Phase 2.
- Phase 4 depends on Phase 3.

---

## 3. Complexity Estimates
- **Phase 1:** Low
- **Phase 2:** Medium
- **Phase 3:** Medium
- **Phase 4:** Low
