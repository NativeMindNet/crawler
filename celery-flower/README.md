# Celery Flower Monitoring for TaxLien Crawler

Real-time monitoring dashboard for Celery-based crawler deployments.

## Quick Start

### 1. Start Base Stack (Celery + Flower)

```bash
# From project root
docker-compose -f celery-flower/docker-compose.yml up -d

# View logs
docker-compose logs -f flower

# Access Flower dashboard
# URL: http://localhost:5555/flower
# Login: flower / flower_password
```

### 2. Scale Workers

```bash
# Scale to 5 workers
docker-compose -f celery-flower/docker-compose.yml up -d --scale worker=5
```

### 3. Start Monitoring Stack (Optional)

```bash
# Start Prometheus and Grafana
docker-compose -f celery-flower/docker-compose.yml -f celery-flower/docker-compose.monitoring.yml up -d

# Access Prometheus: http://localhost:9090
# Access Grafana: http://localhost:3000 (login: admin / grafana_password)
```

## Architecture

```
┌─────────────┐     ┌─────────────┐
│   Worker 1  │     │   Worker N  │
│  (crawler)  │     │  (crawler)  │
└──────┬──────┘     └──────┬──────┘
       │                   │
       └────────┬──────────┘
                │
                ▼
       ┌─────────────────┐
       │  Redis Broker   │
       └────────┬────────┘
                │
       ┌────────┼────────┐
       │        │        │
       ▼        ▼        ▼
   ┌──────┐ ┌──────┐ ┌──────────┐
   │Flower│ │Prometheus│ │Grafana │
   │:5555 │ │ :9090  │ │ :3000  │
   └──────┘ └────────┘ └──────────┘
```

## Components

| Component | Port | Purpose |
|-----------|------|---------|
| Redis | 6379 | Message broker |
| Flower | 5555 | Task monitoring dashboard |
| Prometheus | 9090 | Metrics collection |
| Grafana | 3000 | Dashboards & alerting |

## Configuration

### Celery Event Emission

For Flower to monitor tasks, Celery must emit events. Add to your `celery_app.py` or `tasks.py`:

```python
app.conf.update(
    worker_send_task_events=True,   # Required for Flower
    task_send_sent_events=True,     # Required for Flower
)
```

### Worker Launch

Add `--send-events` flag:

```bash
celery -A tasks worker --loglevel=info --send-events
```

## Operations

### View Task Status

1. Open http://localhost:5555/flower
2. Navigate to "Tasks" tab
3. Click task ID for details

### Retry Failed Tasks

1. Find failed task in Flower
2. Click task ID
3. Click "Retry" button

### View Metrics

**Prometheus** (http://localhost:9090):
```promql
flower_events_total           # All task events
flower_worker_tasks_total     # Tasks per worker
flower_task_runtime_seconds   # Runtime distribution
```

**Grafana** (http://localhost:3000):
- Dashboard: Celery → Flower Overview
- 8 panels: success rate, throughput, runtime, workers

## Troubleshooting

### Flower Not Showing Workers

```bash
# Check worker logs
docker-compose -f celery-flower/docker-compose.yml logs worker

# Verify Redis connection
docker-compose -f celery-flower/docker-compose.yml exec redis redis-cli ping

# Confirm events enabled in tasks.py
grep -n "send_task_events" legacy/legacy-celery/tasks.py
```

### Workers Not Processing Tasks

```bash
# Check task queue
docker-compose -f celery-flower/docker-compose.yml exec redis redis-cli llen celery

# Inspect workers
docker-compose -f celery-flower/docker-compose.yml exec worker celery -A tasks inspect active
```

## Production Deployment

### HTTPS Setup

```bash
# Generate SSL certificate
mkdir -p celery-flower/nginx/ssl
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout celery-flower/nginx/ssl/flower.key \
  -out celery-flower/nginx/ssl/flower.crt
```

### Security Checklist

- [ ] Change default passwords in .env
- [ ] Enable HTTPS (don't use HTTP in production)
- [ ] Restrict /metrics to internal network
- [ ] Use firewall for Redis (don't expose publicly)

## Legacy Code

The actual Celery tasks and platform code remain in `legacy/legacy-celery/`. This directory contains only the monitoring infrastructure.

## References

- [Flower Docs](https://flower.readthedocs.io/)
- [Celery Docs](https://docs.celeryq.dev/)
- [SDD Spec](flows/sdd-crawler-flower/)
