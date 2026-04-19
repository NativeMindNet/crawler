# Requirements: Crawler Control Panel (Django)

**Version:** 3.0
**Status:** DRAFT
**Last Updated:** 2026-04-19

---

## Decision: Django-based Control Panel

Previously, we considered AppSmith but pivoted to Flower + Minimal API. Now, we are standardizing on **Django** for both the API (via Django Ninja) and the Management UI (Control Panel).

**Key shifts:**
- Replace AppSmith with a lightweight Django Control Panel.
- Leverage **Django Admin** for rapid data management.
- Use **Django Templates** or a simple frontend for the operator dashboard.
- Integrate with **Flower** for real-time task monitoring.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       CRAWLER INSTANCE                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────────────┐ │
│  │   Celery    │    │   Celery    │    │      Flower         │ │
│  │    Beat     │───>│   Workers   │    │   (:5555)           │ │
│  │ (Scheduler) │    │ (Scrapers)  │    │   Task Monitoring   │ │
│  └─────────────┘    └──────┬──────┘    └─────────────────────┘ │
│                            │                                    │
│         ┌──────────────────┴──────────────────┐                 │
│         ▼                                     ▼                 │
│  ┌─────────────┐               ┌──────────────────────────────┐ │
│  │    Redis    │               │    Django Control Panel      │ │
│  │   Broker    │               │           (:8000)            │ │
│  └─────────────┘               ├──────────────────────────────┤ │
│                                │ - Django Admin (DB Mgmt)     │ │
│                                │ - Dashboard (Monitoring)     │ │
│                                │ - Ninja API (Integration)    │ │
│                                └──────────────────────────────┘ │
│                                               │                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Functional Requirements

### 1. Dashboard (Monitoring)
- Overview of current crawler state (health, uptime, platform).
- Real-time (or near real-time) queue depth stats.
- Links to Flower for deep-dive task debugging.

### 2. Configuration UI
- View and edit platform configurations.
- Trigger validation for specific platform configs.
- Environment variable management overview.

### 3. Task Management (Django Admin)
- Browse tasks stored in LPM (SQLite).
- Filter tasks by status, platform, or date.
- Manually trigger retries or deletion of tasks via Admin Actions.

### 4. Log Viewer
- Web-based interface to view/search crawler logs.
- Filtering by log level and time range.

### 5. System Controls
- Buttons to restart workers/beat (integrated with System API).
- Toggle between Standalone and On-demand modes (requires restart).

---

## User Stories

### US-1: Unified Management
**As a** crawler operator
**I want** a single web interface to see health, tasks, and logs
**So that** I don't have to switch between CLI, logs files, and different UIs.

### US-2: Fast Data Correction
**As a** developer
**I want** to use Django Admin to quickly fix or delete erroneous tasks in the database
**So that** I can recover from scraping bugs without writing SQL.

### US-3: Configuration Tuning
**As a** system admin
**I want** to update rate limits or proxy settings via the UI
**So that** I can respond to platform changes in real-time.

---

## Implementation Tasks

### Phase 1: Django Integration (3 tasks)
- [ ] Initialize Django Project with minimal settings.
- [ ] Configure SQLite (LPM) as the primary database for Django models.
- [ ] Setup Django Admin for `Task` and `Result` models.

### Phase 2: Control Panel UI (3 tasks)
- [ ] Create a "Dashboard" home page with health metrics.
- [ ] Implement Configuration Edit views.
- [ ] Implement Log Viewer page.

### Phase 3: System Integration (2 tasks)
- [ ] Integrate with Celery/Flower for worker management.
- [ ] Implement restart triggers.

---

## Non-Goals
- Full-blown user management (Basic Auth or single admin user is enough).
- Complex analytics (use Grafana/Prometheus for that).

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
