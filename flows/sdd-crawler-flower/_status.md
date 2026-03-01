# Status: sdd-crawler-flower

## DEPRECATED - MERGED

**Merged Into:** `sdd-crawler-appsmith` v2.0
**Merge Date:** 2026-03-01
**Reason:** Flower is now the primary monitoring UI; AppSmith replaced with "Flower + minimal API"

---

## What Happened

1. `sdd-crawler-architecture` v3.0 adopted Celery-only (removed async mode)
2. `sdd-crawler-appsmith` v2.0 pivoted from AppSmith to Flower
3. Flower requirements now live in `sdd-crawler-appsmith/01-requirements.md`

---

## Implementation Status

The implementation in `celery-flower/` directory remains valid and is referenced by `sdd-crawler-appsmith`.

**Files Created (still valid):**
- `celery-flower/docker-compose.yml` - Redis + Workers + Flower
- `celery-flower/docker-compose.monitoring.yml` - Prometheus + Grafana
- `celery-flower/prometheus/prometheus.yml` - Metrics scrape config
- `celery-flower/grafana/dashboards/flower-overview.json` - Dashboard
- `celery-flower/nginx/flower.conf` - Reverse proxy config

---

## Historical Context

See `01-requirements.md` in this directory for original Flower requirements.

These requirements are now part of `sdd-crawler-appsmith` v2.0 which consolidates:
- Flower for task monitoring
- Minimal FastAPI endpoints for config/logs/restart

---

## See Also

- `sdd-crawler-appsmith/_status.md` - Current home for Flower requirements
- `sdd-crawler-architecture/_status.md` - v3.0 Celery-only architecture
- `SDD-CONSOLIDATION.md` - Consolidation plan
