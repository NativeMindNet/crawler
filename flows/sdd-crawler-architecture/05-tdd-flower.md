# TDD: Flower Monitoring Configuration

> **Version:** 1.0  
> **Date:** 2026-03-01  
> **Task:** 2.6 - Flower Monitoring  
> **Files:** `config/flower/flower.conf.py`, `docker-compose.flower.yml`

---

## VDD: Value-Driven Design

### Business Value

| Value | Description | Metric |
|-------|-------------|--------|
| **Visibility** | Real-time view of Celery task execution | Instant issue detection |
| **Debugging** | Inspect task arguments, results, errors | 50% faster debugging |
| **Operations** | Monitor worker health and capacity | Proactive scaling |
| **Analytics** | Track task throughput and latency | Data-driven optimization |

### User Stories

#### US-1: Task Monitoring
```
As an operator
I want to see real-time task execution status
So that I can monitor crawler progress

Acceptance Criteria:
- Given Celery workers are processing tasks
- When I open Flower dashboard
- Then I can see pending, running, and completed tasks
- And I can see task arguments and results
```

#### US-2: Worker Monitoring
```
As an operator
I want to see worker health and status
So that I know if workers are alive

Acceptance Criteria:
- Given 3 Celery workers are running
- When I open Flower dashboard
- Then I can see all 3 workers with status "Online"
- And I can see tasks processed per worker
```

#### US-3: Task Retry
```
As an operator
I want to retry failed tasks from the dashboard
So that I can recover from transient errors

Acceptance Criteria:
- Given a task failed with error
- When I click "Retry" in Flower
- Then the task is re-queued
- And I can see the retry in task history
```

---

## DDD: Domain-Driven Design

### Ubiquitous Language

| Term | Definition |
|------|------------|
| **Flower** | Celery monitoring web application |
| **Task** | Unit of work executed by Celery worker |
| **Worker** | Celery worker process executing tasks |
| **Broker** | Redis message broker for task queue |
| **Event** | Celery task event (started, succeeded, failed) |
| **Dashboard** | Flower web UI for monitoring |

### Bounded Context

```
┌─────────────────────────────────────────────────────────────┐
│                   FLOWER MONITORING CONTEXT                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Components:                                                 │
│  - Flower Server (monitoring application)                   │
│  - Celery Events (task lifecycle events)                    │
│  - Prometheus Metrics (optional export)                     │
│                                                               │
│  Configuration:                                              │
│  - Flower Config (Python module)                            │
│  - Docker Compose (deployment)                              │
│  - Authentication (basic auth / OAuth)                      │
│                                                               │
│  Integration Points:                                         │
│  - Celery Broker (Redis)                                    │
│  - Celery Workers (event publishers)                        │
│  - External Monitoring (Prometheus, Grafana)                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## TDD: Test-Driven Development

### Configuration Tests

```python
# crawler/tests/test_flower_config.py
import pytest
import os
from pathlib import Path


class TestFlowerConfiguration:
    """Test Flower configuration"""
    
    def test_flower_config_exists(self):
        """Given project, when checked, then flower config exists"""
        config_path = Path("config/flower/flower.conf.py")
        
        assert config_path.exists(), "Flower configuration file should exist"
    
    def test_flower_config_valid_python(self):
        """Given config file, when checked, then it's valid Python"""
        config_path = Path("config/flower/flower.conf.py")
        
        # Should compile without errors
        with open(config_path, "r") as f:
            code = f.read()
        
        compile(code, str(config_path), "exec")
    
    def test_flower_docker_compose_exists(self):
        """Given project, when checked, then flower docker-compose exists"""
        compose_path = Path("docker-compose.flower.yml")
        
        assert compose_path.exists(), "Flower docker-compose should exist"
    
    def test_flower_docker_compose_valid_yaml(self):
        """Given compose file, when checked, then it's valid YAML"""
        import yaml
        
        compose_path = Path("docker-compose.flower.yml")
        
        with open(compose_path, "r") as f:
            data = yaml.safe_load(f)
        
        assert "services" in data
        assert "flower" in data["services"]


class TestFlowerIntegration:
    """Test Flower integration with Celery"""
    
    def test_flower_connects_to_redis(self):
        """Given Flower running, when started, then connects to Redis"""
        # This would be an integration test
        # For now, verify configuration has Redis settings
        config_path = Path("config/flower/flower.conf.py")
        
        with open(config_path, "r") as f:
            content = f.read()
        
        assert "broker_api" in content or "REDIS" in content
    
    def test_flower_receives_events(self):
        """Given Flower running, when tasks execute, then events are received"""
        # Integration test - verify Celery is configured to send events
        from crawler.celery_app import app
        
        # Celery should be configured to send events
        assert app.conf.task_send_sent_event is True
        assert app.conf.worker_send_task_events is True
    
    def test_flower_authentication_configured(self):
        """Given Flower, when checked, then authentication is configured"""
        config_path = Path("config/flower/flower.conf.py")
        
        with open(config_path, "r") as f:
            content = f.read()
        
        # Should have some form of authentication
        assert "basic_auth" in content or "auth" in content or "FLOWER_BASIC_AUTH" in content
```

---

## Implementation

### Flower Configuration File

```python
# config/flower/flower.conf.py
"""
Flower configuration for Celery monitoring.

Documentation: https://flower.readthedocs.io/en/latest/config.html

Environment Variables:
    FLOWER_BASIC_AUTH: username:password for basic auth
    FLOWER_PORT: Flower server port (default: 5555)
    REDIS_HOST: Redis host (default: redis)
    REDIS_PORT: Redis port (default: 6379)
    REDIS_PASSWORD: Redis password (optional)
"""

import os
from datetime import timedelta


# =============================================================================
# Server Configuration
# =============================================================================

# Flower server port
PORT = int(os.environ.get("FLOWER_PORT", "5555"))

# Server address
ADDRESS = "0.0.0.0"

# SSL configuration (optional for production)
# SSL_KEYFILE = "/path/to/key.pem"
# SSL_CERTFILE = "/path/to/cert.pem"


# =============================================================================
# Celery Broker Configuration
# =============================================================================

# Redis broker configuration
REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_PASSWORD = os.environ.get("REDIS_PASSWORD", "")
REDIS_DB = int(os.environ.get("REDIS_DB", "0"))

# Broker URL for Celery
BROKER_API = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"

# If password is set, update BROKER_API
if REDIS_PASSWORD:
    BROKER_API = f"redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"


# =============================================================================
# Authentication
# =============================================================================

# Basic authentication (username:password)
# Set via environment variable: FLOWER_BASIC_AUTH=user:pass
BASIC_AUTH = os.environ.get("FLOWER_BASIC_AUTH", "")

# Alternative: OAuth configuration
# OAUTH2_KEY = os.environ.get("OAUTH2_KEY", "")
# OAUTH2_SECRET = os.environ.get("OAUTH2_SECRET", "")
# OAUTH2_REDIRECT_URI = os.environ.get("OAUTH2_REDIRECT_URI", "")
# OAUTH2_SCOPE = ["email", "profile"]

# Google OAuth example:
# OAUTH2_PROVIDER = "google"
# OAUTH2_AUTHORIZATION_URL = "https://accounts.google.com/o/oauth2/v2/auth"
# OAUTH2_ACCESS_TOKEN_URL = "https://oauth2.googleapis.com/token"
# OAUTH2_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"


# =============================================================================
# Security
# =============================================================================

# Enable secure cookies in production
SECURE_COOKIE = os.environ.get("FLOWER_SECURE_COOKIE", "false").lower() == "true"

# Cookie secret (generate a random string for production)
COOKIE_SECRET = os.environ.get("FLOWER_COOKIE_SECRET", "dev-secret-change-in-production")

# XSRF protection
XSRF_COOKIE = True


# =============================================================================
# Monitoring & Metrics
# =============================================================================

# Enable Prometheus metrics export
PROMETHEUS_ENABLED = os.environ.get("FLOWER_PROMETHEUS", "false").lower() == "true"
PROMETHEUS_PORT = int(os.environ.get("FLOWER_PROMETHEUS_PORT", "5556"))

# Task event retention
# How long to keep task events in memory
STATE_SAVE_INTERVAL = timedelta(minutes=5)

# Max number of tasks to keep in memory
MAX_TASKS = 10000

# Max number of workers to track
MAX_WORKERS = 100


# =============================================================================
# UI Customization
# =============================================================================

# Custom branding
BRAND = "Tax Lien Crawler"

# Custom logo (URL path)
# LOGO_URL = "/static/logo.png"

# Custom CSS
# CUSTOM_CSS = "/static/custom.css"

# Default time range for task graphs (in hours)
DEFAULT_GRAPH_INTERVAL = 24  # 24 hours


# =============================================================================
# Performance Tuning
# =============================================================================

# Number of concurrent connections
MAX_WORKERS_CONNECTIONS = 100

# Websocket ping interval (seconds)
WEBSOCKET_PING_INTERVAL = 30

# Cache timeout for broker info (seconds)
BROKER_API_CACHE_TIMEOUT = 60


# =============================================================================
# Logging
# =============================================================================

# Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_LEVEL = os.environ.get("FLOWER_LOG_LEVEL", "INFO")

# Log format
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Log to file (optional)
# LOG_FILE = "/var/log/flower/flower.log"


# =============================================================================
# URL Configuration
# =============================================================================

# URL prefix (useful when behind reverse proxy)
URL_PREFIX = os.environ.get("FLOWER_URL_PREFIX", "")

# Example: URL_PREFIX = "/flower" would make Flower available at /flower


# =============================================================================
# Persistent Storage (optional)
# =============================================================================

# Enable persistent storage for task history
# PERSISTENT = True
# DB = "/data/flower/flower.db"  # SQLite database path


# =============================================================================
# Integration with External Systems
# =============================================================================

# Google Analytics (optional)
# GOOGLE_ANALYTICS_ID = "UA-XXXXX-Y"

# Sentry error tracking (optional)
# SENTRY_DSN = os.environ.get("SENTRY_DSN", "")


# =============================================================================
# Development Settings
# =============================================================================

# Debug mode (DO NOT enable in production)
DEBUG = os.environ.get("FLOWER_DEBUG", "false").lower() == "true"

# Enable testing mode
TESTING = os.environ.get("FLOWER_TESTING", "false").lower() == "true"


# =============================================================================
# Production Checklist
# =============================================================================
#
# Before deploying to production:
#
# [ ] Set FLOWER_BASIC_AUTH to strong credentials
# [ ] Set FLOWER_COOKIE_SECRET to random 32+ character string
# [ ] Set FLOWER_SECURE_COOKIE = True
# [ ] Set FLOWER_URL_PREFIX if behind reverse proxy
# [ ] Configure SSL (SSL_KEYFILE, SSL_CERTFILE)
# [ ] Set LOG_LEVEL to WARNING or ERROR
# [ ] Configure persistent storage (PERSISTENT = True)
# [ ] Set up monitoring/alerting on Flower health
# [ ] Restrict network access to Flower port (firewall)
# [ ] Enable Prometheus metrics for dashboards
#
# =============================================================================
```

---

### Docker Compose for Flower

```yaml
# docker-compose.flower.yml
version: '3.8'

services:
  flower:
    image: mher/flower:2.0.0
    container_name: crawler-flower
    restart: unless-stopped
    
    environment:
      # Celery broker (Redis)
      - CELERY_BROKER_URL=redis://redis:6379/0
      
      # Flower configuration
      - FLOWER_PORT=5555
      - FLOWER_BASIC_AUTH=${FLOWER_USER:-admin}:${FLOWER_PASSWORD:-admin}
      - FLOWER_URL_PREFIX=${FLOWER_URL_PREFIX:-}
      
      # Security (set these in production!)
      - FLOWER_COOKIE_SECRET=${FLOWER_COOKIE_SECRET:-change-me-in-production}
      - FLOWER_SECURE_COOKIE=${FLOWER_SECURE_COOKIE:-false}
      
      # Logging
      - FLOWER_LOG_LEVEL=${FLOWER_LOG_LEVEL:-INFO}
      
      # Prometheus metrics (optional)
      - FLOWER_PROMETHEUS=${FLOWER_PROMETHEUS:-false}
      - FLOWER_PROMETHEUS_PORT=5556
    
    ports:
      - "${FLOWER_PORT:-5555}:5555"
      - "${FLOWER_PROMETHEUS_PORT:-5556}:5556"  # Prometheus metrics
    
    volumes:
      # Mount configuration
      - ./config/flower/flower.conf.py:/app/flowerconfig.py:ro
      
      # Optional: persistent storage for task history
      - flower-data:/data
    
    networks:
      - crawler-network
    
    depends_on:
      - redis
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:5555/api/workers"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    
    labels:
      - "app=crawler"
      - "component=flower"
      - "monitoring.enabled=true"

# Optional: Persistent storage for task history
volumes:
  flower-data:
    driver: local

networks:
  crawler-network:
    external: true
```

---

### Updated Celery Configuration

```python
# crawler/celery_app.py (modification)
from celery import Celery
from celery.signals import setup_logging
import os

# Create Celery app
app = Celery(
    'crawler',
    broker=os.environ.get('CELERY_BROKER_URL', 'redis://redis:6379/0'),
    backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://redis:6379/0'),
    include=['crawler.tasks']
)

# Configuration
app.conf.update(
    # Task settings
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # Flower monitoring - CRITICAL for task events
    task_send_sent_event=True,  # Send task sent events
    task_send_created_event=True,  # Send task created events
    
    # Worker settings
    worker_send_task_events=True,  # Send task events from worker
    worker_prefetch_multiplier=1,  # Fair task distribution
    
    # Priority queues
    task_routes={
        'crawler.tasks.scrape_url': {'queue': 'high'},
        'crawler.tasks.parse_html': {'queue': 'default'},
        'crawler.tasks.save_result': {'queue': 'low'},
    },
    
    # Rate limiting (annotations)
    task_annotations={
        'crawler.tasks.scrape_url': {'rate_limit': '10/m'},
        'crawler.tasks.bulk_import': {'rate_limit': '1/h'},
    },
    
    # Retry settings
    task_acks_late=True,  # Acknowledge task after completion
    task_reject_on_worker_lost=True,  # Re-queue on worker death
    task_default_retry_delay=30,  # 30 seconds between retries
    task_max_retries=3,
)


# Flower integration verification
@app.on_after_configure.connect
def setup_flower_monitoring(sender, **kwargs):
    """Verify Flower monitoring is properly configured"""
    import logging
    logger = logging.getLogger(__name__)
    
    # Verify event settings
    if not sender.conf.task_send_sent_event:
        logger.warning("Flower monitoring: task_send_sent_event is disabled")
    
    if not sender.conf.worker_send_task_events:
        logger.warning("Flower monitoring: worker_send_task_events is disabled")
    
    logger.info("Flower monitoring configured successfully")
```

---

### Kubernetes Deployment (Optional)

```yaml
# k8s/flower-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: flower
  labels:
    app: crawler
    component: flower
spec:
  replicas: 1
  selector:
    matchLabels:
      app: crawler
      component: flower
  template:
    metadata:
      labels:
        app: crawler
        component: flower
    spec:
      containers:
      - name: flower
        image: mher/flower:2.0.0
        ports:
        - containerPort: 5555
          name: http
        - containerPort: 5556
          name: prometheus
        env:
        - name: CELERY_BROKER_URL
          valueFrom:
            secretKeyRef:
              name: crawler-secrets
              key: redis-url
        - name: FLOWER_BASIC_AUTH
          valueFrom:
            secretKeyRef:
              name: flower-secrets
              key: basic-auth
        - name: FLOWER_COOKIE_SECRET
          valueFrom:
            secretKeyRef:
              name: flower-secrets
              key: cookie-secret
        volumeMounts:
        - name: flower-config
          mountPath: /app/flowerconfig.py
          subPath: flower.conf.py
          readOnly: true
        - name: flower-data
          mountPath: /data
        livenessProbe:
          httpGet:
            path: /api/workers
            port: 5555
          initialDelaySeconds: 30
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /api/workers
            port: 5555
          initialDelaySeconds: 10
          periodSeconds: 10
        resources:
          requests:
            memory: "128Mi"
            cpu: "100m"
          limits:
            memory: "256Mi"
            cpu: "200m"
      volumes:
      - name: flower-config
        configMap:
          name: flower-config
      - name: flower-data
        persistentVolumeClaim:
          claimName: flower-data-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: flower
  labels:
    app: crawler
    component: flower
spec:
  selector:
    app: crawler
    component: flower
  ports:
  - port: 5555
    targetPort: 5555
    name: http
  - port: 5556
    targetPort: 5556
    name: prometheus
  type: ClusterIP  # Use LoadBalancer or Ingress for external access
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: flower
  annotations:
    nginx.ingress.kubernetes.io/auth-type: basic
    nginx.ingress.kubernetes.io/auth-secret: flower-auth
    nginx.ingress.kubernetes.io/auth-realm: "Authentication Required"
spec:
  rules:
  - host: flower.crawler.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: flower
            port:
              number: 5555
```

---

## Usage Guide

### Starting Flower

```bash
# Docker Compose
docker-compose -f docker-compose.celery.yml -f docker-compose.flower.yml up -d flower

# Access dashboard
open http://localhost:5555

# Login with credentials from FLOWER_BASIC_AUTH
```

### Flower API

```bash
# Get worker status
curl http://admin:admin@localhost:5555/api/workers

# Get task info
curl http://admin:admin@localhost:5555/api/task/info/<task_id>

# Retry a task
curl -X POST http://admin:admin@localhost:5555/api/task/retry/<task_id>
```

### Prometheus Metrics

```bash
# Scrape metrics
curl http://localhost:5556/metrics

# Example metrics:
# flower_tasks_succeeded
# flower_tasks_failed
# flower_workers_online
```

---

## Acceptance Criteria Checklist

- [ ] Flower configuration file created
- [ ] Docker Compose for Flower created
- [ ] Celery configured to send events
- [ ] Authentication configured
- [ ] Health checks configured
- [ ] Documentation complete
- [ ] Tests passing
- [ ] Production checklist documented
