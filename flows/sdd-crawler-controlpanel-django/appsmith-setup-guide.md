# AppSmith UI Setup Guide

> Version: 1.0
> Created: 2026-03-01

This guide explains how to set up the AppSmith UI for the Universal Crawler.

---

## Quick Start

1. **Start the stack:**
   ```bash
   docker-compose up -d
   ```

2. **Access AppSmith:**
   - Open http://localhost:3000
   - Complete initial setup (admin user)

3. **Create a new application:**
   - Click "Create New" → "Application"
   - Name it "Crawler Dashboard"

4. **Create API datasource:**
   - Click "Datasources" → "Create New" → "API"
   - Name: `Crawler API`
   - Base URL: `http://crawler-qpublic:8000` (or `http://localhost:8001` for local dev)
   - Authentication: None (single-user mode)
   - Click "Save"

---

## Page 1: Dashboard

### Layout

Create a new page named "Dashboard" with the following widgets:

| Widget | Type | Properties |
|--------|------|------------|
| `txt_title` | Text | `Crawler Dashboard - {{appsmith.store.platform}}` |
| `card_pending` | Stat Box | Label: `Pending`, Value: `{{api_tasks.data.pending}}` |
| `card_completed` | Stat Box | Label: `Completed`, Value: `{{api_tasks.data.processing}}` (use processing for now) |
| `card_failed` | Stat Box | Label: `Failed`, Value: `{{api_health.data.queue_details.failed}}` |
| `gauge_cpu` | Progress | Value: `{{api_metrics.data.cpu_percent}}`, Max: 100 |
| `gauge_memory` | Progress | Value: `{{api_metrics.data.memory_percent}}`, Max: 100 |
| `txt_uptime` | Text | `Uptime: {{api_metrics.data.uptime_human}}` |
| `table_recent` | Table | Items: `{{api_tasks_recent.data.tasks}}` |

### API Queries

**`api_health`:**
- Method: GET
- Path: `/health`
- Auto-refresh: Every 30s

**`api_metrics`:**
- Method: GET
- Path: `/metrics`
- Auto-refresh: Every 10s

**`api_tasks`:**
- Method: GET
- Path: `/tasks?limit=1`
- Auto-refresh: Every 30s

**`api_tasks_recent`:**
- Method: GET
- Path: `/tasks?status=completed&limit=10&sort_by=completed_at&sort_order=desc`
- Auto-refresh: Every 30s

---

## Page 2: Tasks

### Layout

Create a new page named "Tasks" with:

| Widget | Type | Properties |
|--------|------|------------|
| `table_tasks` | Table | Items: `{{api_tasks_list.data.tasks}}`, Pagination: true |
| `dropdown_status` | Select | Options: `All, pending, processing, completed, failed` |
| `input_search` | Input | Placeholder: `Search by URL or ID` |
| `btn_refresh` | Button | onClick: `{{api_tasks_list.run()}}` |
| `btn_retry` | Button | Visible: `{{table_tasks.selectedRow.status === 'failed'}}` |
| `btn_retry_all` | Button | onClick: `{{api_retry_bulk.run()}}` |
| `modal_details` | Modal | Shows task details |

### API Queries

**`api_tasks_list`:**
- Method: GET
- Path: `/tasks?status={{dropdown_status.value === 'All' ? '' : dropdown_status.value}}&limit={{table_tasks.pageSize}}&offset={{(table_tasks.page - 1) * table_tasks.pageSize}}`
- Auto-refresh: Manual

**`api_retry_single`:**
- Method: POST
- Path: `/tasks/{{table_tasks.selectedRow.id}}/retry`
- Triggered by: `btn_retry` onClick

**`api_retry_bulk`:**
- Method: POST
- Path: `/tasks/retry-bulk?status=failed&limit=100`
- Triggered by: `btn_retry_all` onClick

---

## Page 3: Health

### Layout

Create a new page named "Health" with:

| Widget | Type | Properties |
|--------|------|------------|
| `gauge_cpu` | Progress | Value: `{{api_metrics.data.cpu_percent}}` |
| `gauge_memory` | Progress | Value: `{{api_metrics.data.memory_percent}}` |
| `chart_cpu` | Line Chart | Data: `{{api_metrics_history.data}}` |
| `chart_memory` | Line Chart | Data: `{{api_metrics_history.data}}` |
| `txt_mode` | Text | `Mode: {{api_mode.data.mode}}` |
| `link_flower` | Link | Text: `Open Flower Dashboard`, URL: `{{api_mode.data.flower_url}}` |

### API Queries

**`api_mode`:**
- Method: GET
- Path: `/system/mode`
- Auto-refresh: On page load

**`api_metrics`:**
- Method: GET
- Path: `/metrics`
- Auto-refresh: Every 10s

---

## Page 4: Config

### Layout

Create a new page named "Config" with:

| Widget | Type | Properties |
|--------|------|------------|
| `json_editor` | JSON Editor | Default: `{{api_config.data}}` |
| `btn_save` | Button | onClick: `{{api_config_save.run()}}` |
| `btn_restart` | Button | Visible: `{{api_config_save.isSuccess}}`, onClick: `{{api_restart.run()}}` |
| `alert_success` | Alert | Visible: `{{api_config_save.isSuccess}}`, Message: `Config saved successfully` |

### API Queries

**`api_config`:**
- Method: GET
- Path: `/config`

**`api_config_save`:**
- Method: PUT
- Path: `/config`
- Body: `{{json_editor.value}}`

**`api_restart`:**
- Method: POST
- Path: `/system/restart`
- Body: `{"reason": "Config change via AppSmith", "delay_seconds": 5}`

---

## Page 5: Logs

### Layout

Create a new page named "Logs" with:

| Widget | Type | Properties |
|--------|------|------------|
| `table_logs` | Table | Items: `{{api_logs.data.entries}}`, Pagination: true |
| `dropdown_level` | Select | Options: `ALL, INFO, WARN, ERROR` |
| `input_search` | Input | Placeholder: `Search logs...` |
| `btn_refresh` | Button | onClick: `{{api_logs.run()}}` |

### API Queries

**`api_logs`:**
- Method: GET
- Path: `/logs?level={{dropdown_level.value === 'ALL' ? '' : dropdown_level.value}}&search={{input_search.text}}&page={{table_logs.page}}&page_size={{table_logs.pageSize}}`
- Auto-refresh: Manual

---

## Styling

### Color Scheme

- Primary: `#4E6DFF` (AppSmith default)
- Success: `#03B365`
- Warning: `#F5870B`
- Error: `#E03131`

### Responsive Design

- Use container widgets for grouping
- Set min-width for tables: `800px`
- Use auto-layout for responsive rows

---

## Testing

After creating all pages:

1. Navigate to each page
2. Verify API calls succeed (check Developer Tools → Network)
3. Test retry functionality with a failed task
4. Test config save (use a test config value)
5. Verify logs display correctly

---

## Troubleshooting

### API Connection Failed

**Problem:** AppSmith cannot reach crawler API

**Solution:**
- For Docker: Use `http://crawler-qpublic:8000` as base URL
- For local dev: Use `http://localhost:8001`
- Check container networking: `docker network ls`

### CORS Errors

**Problem:** Browser blocks API requests

**Solution:**
- Crawler API already has CORS enabled (`allow_origins=["*"]`)
- Check middleware is loaded in `crawler/api/app.py`

### Flower Link Not Showing

**Problem:** Flower link hidden on Health page

**Solution:**
- Flower is only available in Celery mode
- Set `MODE=celery` environment variable
- Ensure `FLOWER_URL` is set

---

## Export/Import

To backup or share your AppSmith application:

1. **Export:**
   - Click Settings (gear icon) → "Export"
   - Save JSON file

2. **Import:**
   - Click "Create New" → "Import from file"
   - Select JSON export file

---

## Next Steps

After basic setup:

1. Add authentication (if multi-user)
2. Create custom dashboards for specific platforms
3. Set up alerts for failed tasks
4. Integrate with external monitoring (Grafana)
