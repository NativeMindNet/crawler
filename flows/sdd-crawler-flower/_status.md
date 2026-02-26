# Status: sdd-crawler-flower

## Current Phase

SPECIFICATIONS

## Phase Status

DRAFTING

## Last Updated

2026-02-26 by Qwen (SDD mode)

## Blockers

- None - requirements approved, proceeding to specs

## Progress

- [x] Requirements drafted (initial analysis complete)
- [x] Requirements approved
- [ ] Specifications drafted
- [ ] Specifications approved
- [ ] Plan drafted
- [ ] Plan approved
- [ ] Implementation started
- [ ] Implementation complete

## Context Notes

Key decisions and context for resuming:

- **Purpose**: This SDD flow captures Flower monitoring requirements that were NOT in the main `sdd-crawler` spec
- **Legacy Source**: Analysis of `/legacy/legacy-celery/` (flower==2.0.1 in requirements.txt, dev_run_flower.sh)
- **Deployment Mode**: Flower is **Celery-mode only** - not needed for SQLite standalone mode
- **Core Value**: Real-time visibility into tasks, workers, queue depth, and performance metrics
- **Authentication**: Must support Basic Auth (minimum) and OAuth (preferred)
- **Prometheus**: Optional but recommended for Grafana integration

### Flower Features to Support:

1. **Real-Time Monitoring** - Live task progress and worker status
2. **Task Administration** - Retry failed tasks, revoke stuck tasks
3. **Worker Dashboard** - Worker health, concurrency, uptime
4. **Performance Analytics** - Success rates, runtime distribution, throughput
5. **Prometheus Export** - Metrics endpoint for external monitoring
6. **Secure Access** - HTTP Basic Auth and OAuth (Google/GitHub/GitLab/Okta)
7. **Docker Integration** - Flower as separate container in docker-compose

### Legacy Components Analyzed:

- `requirements.txt`: Flower 2.0.1 dependency
- `dev_run_flower.sh`: Development launcher script (needs analysis)
- `celery_app.py`: Celery app configuration (must enable events for Flower)

### Celery Event Requirements:

```python
app.conf.update(
    worker_send_task_events=True,   # Required for Flower
    task_send_sent_events=True,     # Required for Flower
)
```

## Open Questions (Need Resolution)

1. **Q1 - Authentication**: Basic Auth, OAuth, or both?
2. **Q2 - OAuth Provider**: Google, GitHub, GitLab, or Okta?
3. **Q3 - Port Exposure**: Public (5555) or internal (via reverse proxy)?
4. **Q4 - Prometheus**: Required for MVP or optional add-on?
5. **Q5 - Custom Views**: Need crawler-specific tabs/metrics?
6. **Q6 - Alerting**: Flower sends alerts or just displays metrics?
7. **Q7 - Persistence**: How long to retain task history in memory?

## Next Actions

1. **User reviews requirements** - Confirm scope and user stories
2. **Resolve open questions** - Q1-Q7 need answers before specs
3. **Move to SPECIFICATIONS phase** - Design Flower architecture

## Fork History

- This is a new SDD flow spun off from `sdd-crawler-celery` analysis
- Reason: Flower monitoring is a significant feature requiring its own spec
- Related: `sdd-crawler-celery` (distributed task queue requirements)
