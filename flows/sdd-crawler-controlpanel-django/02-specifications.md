# Specifications: Crawler Control Panel (Django UI)

**Version:** 3.0
**Status:** DRAFT
**Last Updated:** 2026-04-19

---

## 1. Architectural Overview

The control panel is a **Django** application providing the Management UI. It runs alongside the crawler and interacts with the same SQLite (LPM) database.

### 1.1. Technology Stack
- **Framework:** Django 5.x
- **UI:** Django Admin + Custom Views (Django Templates + Bootstrap 5)
- **Database:** SQLite (LPM - Local Persistence Manager)
- **Integration:** Directly uses LPM models and repo classes.

### 1.2. Component Mapping

| Feature | Implementation | Description |
|---------|----------------|-------------|
| **Operator Dashboard** | Custom View | High-level metrics (throughput, health) |
| **Task Management** | Django Admin | CRUD on tasks and results |
| **Log UI** | Custom View | Searchable and filterable log entries |
| **System Controls** | Custom View / Admin Actions | Buttons for restart and queue management |

---

## 2. Data Integration

### 3.1. Django Models (Unmanaged)
To avoid interfering with the crawler's direct SQLite access via `aiosqlite`, Django will map to existing tables:

- `TaskModel` -> `standalone_tasks` or `ondemand_tasks`
- `ResultModel` -> `parsed_result`
- `LogModel` -> `logs`

### 3.2. Configuration Access
The UI will use the existing `ConfigLoader` to display platform settings but will not necessarily use Django models for these files.

---

## 3. UI Specifications

### 3.1. Dashboard Widgets
- **Health Summary**: Simple cards showing status of Worker, Beat, and API.
- **Queue Stats**: Bar chart showing tasks by status (Pending, Processing, Completed, Failed).
- **Recent Errors**: List of the last 5 error-level logs with links to affected tasks.

### 3.2. Django Admin Enhancements
- **List Filters**: Status, Platform, Created Date.
- **Search Fields**: URL, Task ID, Parcel ID.
- **Actions**:
    - `retry_selected_tasks`: Re-queues tasks in LPM.
    - `export_results_to_json`: Triggers a bulk export.

---

## 4. Implementation Strategy

1.  **Phase 1: Foundation**
    - Create `crawler/controlpanel/` Django app.
    - Setup `settings.py` for SQLite integration.
2.  **Phase 2: Model Mapping**
    - Define models in `crawler/controlpanel/models.py`.
    - Setup Admin registration.
3.  **Phase 3: Custom UI Implementation**
    - Implement the Dashboard view and templates.
    - Implement the Log Viewer.
4.  **Phase 4: Final Integration**
    - Add to `docker-compose.yml` as a separate UI service or merged with the API.
