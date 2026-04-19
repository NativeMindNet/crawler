# Requirements: Crawler Control Panel (Django)

**Version:** 4.0
**Status:** DRAFT
**Last Updated:** 2026-04-19

---

## 1. Goal

Implement a Django-based management interface for the crawler. This replaces the previous AppSmith proposal with a native Python solution that integrates directly with the crawler's SQLite database (LPM).

## 2. Scope

### In Scope
- **Django Admin Integration**: Rapid management of Tasks, Results, and Logs.
- **Operator Dashboard**: High-level visual metrics (health, throughput, error rates).
- **Log Viewer**: Web UI for searching and filtering crawler logs.
- **System Actions**: UI triggers for restarting workers or clearing queues.

### Out of Scope
- **API Migration**: Handled separately in `sdd-crawler-api-django-ninja`.
- **Crawler Logic**: Scrapers and parsers remain unchanged.

---

## 3. User Stories

### US-1: Database Management
**As a** developer
**I want** to use Django Admin to browse and edit tasks in the LPM database
**So that** I can fix data issues or re-queue tasks manually without writing SQL.

### US-2: Visual Monitoring
**As a** crawler operator
**I want** a dashboard showing current health and scraping progress
**So that** I can quickly see if the system is running correctly.

### US-3: Log Analysis
**As a** developer
**I want** to search and filter logs through a web interface
**So that** I can diagnose scraping failures on the go.

---

## 4. Functional Requirements

### FR-1: Managed Database Access
- Map existing SQLite tables (`standalone_tasks`, `parsed_result`, `logs`) to Django Models.
- Use `managed = False` where appropriate to avoid interfering with existing table structures if necessary, or provide a clean migration path.

### FR-2: Custom Dashboard
- A "Home" view showing:
    - Current mode (Standalone/On-demand).
    - Success/Failure ratios (last 24h).
    - Queue depth per platform.
    - System health (CPU/Memory) - integrated with local metrics.

### FR-3: Action Integration
- Implement Django Admin "Actions" to:
    - Bulk retry selected tasks.
    - Export results to CSV/JSON.
    - Archive old data.

---

## 5. Non-Goals
- User authentication beyond standard Django Auth.
- Real-time WebSockets (polling is sufficient for the dashboard).
