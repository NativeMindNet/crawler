# Specifications: Tax Lien Parser CI/CD

> Version: 1.0
> Status: DRAFT
> Last Updated: 2026-02-12
> Requirements: ./01-requirements.md

## Overview

CI/CD система для автоматического деплоя taxlien-parser на инстансы prod/dev/stage через GitHub Actions с self-hosted runners.

**Ключевые особенности:**
- Мульти-платформенность: Linux (Ubuntu) + macOS (stage, иногда dev)
- External volumes для БД и raw data — данные на хосте, персистентность
- Отдельный IP для Docker — изоляция от других проектов
- Запуск нескольких окружений на одном сервере через изоляцию по IP и тегам

## Multi-Platform Support

### Platform Matrix

| Platform | Docker | DEPLOY_DIR | DATA_DIR | BIND_IP |
|----------|--------|------------|----------|---------|
| Linux/Ubuntu | Docker Engine | `/opt/taxlien-parser` | `${DEPLOY_DIR}/{env}/data` | Выделенный IP (10.x.x.x) |
| macOS | Docker Desktop | `~/taxlien-parser` | `${DEPLOY_DIR}/{env}/data` | 127.0.0.1 |

### Configuration per Platform

**Linux Runner:**
```bash
export DEPLOY_DIR=/opt/taxlien-parser
export DATA_DIR=${DEPLOY_DIR}/${ENV_NAME}/data
```

**macOS Runner:**
```bash
export DEPLOY_DIR=~/taxlien-parser
export DATA_DIR=${DEPLOY_DIR}/${ENV_NAME}/data
```

## Affected Systems

| System | Impact | Notes |
|--------|--------|-------|
| `.github/workflows/` | Create | deploy.yml для деплоя |
| `docker-compose.yml` | Create/Modify | Параметризация: IP, порты, теги, external volumes |
| `docker-compose.dev.yml` | Modify | Адаптация или база для CI/CD compose |
| `.env.example` | Create | Шаблон переменных окружения |

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    GitHub Repository (taxlien-parser)             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │ branch:prod │  │ branch:dev  │  │ branch:stage│              │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘              │
│         │                │                │                      │
│         └────────────────┼────────────────┘                      │
│                          ▼                                       │
│              ┌───────────────────────┐                          │
│              │  .github/workflows/   │                          │
│              │     deploy.yml        │                          │
│              └───────────┬───────────┘                          │
└──────────────────────────┼──────────────────────────────────────┘
                           │ triggers
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Server: Prod   │ │  Server: Dev    │ │  Server: Stage   │
│  (Linux)        │ │  (Linux)        │ │  (macOS/Linux)   │
│  ┌───────────┐  │ │  ┌───────────┐  │ │  ┌───────────┐  │
│  │ GH Runner │  │ │  │ GH Runner │  │ │  │ GH Runner │  │
│  │ label:prod│  │ │  │ label:dev │  │ │  │label:stage│  │
│  └─────┬─────┘  │ │  └─────┬─────┘  │ │  └─────┬─────┘  │
│        ▼        │ │        ▼        │ │        ▼        │
│ /opt/taxlien-   │ │ /opt/taxlien-   │ │ ~/taxlien-      │
│   parser/prod/  │ │   parser/dev/   │ │   parser/stage/ │
│   ├─ .env       │ │   ├─ .env       │ │   ├─ .env       │
│   ├─ data/      │ │   ├─ data/      │ │   ├─ data/      │
│   │  └─raw      │ │   │  └─raw      │ │   │  └─raw      │
│   └─ ...        │ │   └─ ...        │ │   └─ ...        │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### External Volumes (Data Persistence)

```
┌─────────────────────────────────────────────────────────────┐
│                    Host Filesystem                           │
│                                                             │
│  ${DEPLOY_DIR}/{env}/data/                                  │
│  └── raw/          ← orchestrator/storage (HTML, JSON)      │
│      Mount: data/raw → /app/orchestrator/storage             │
│                                                             │
│  Gateway (postgres, redis) — деплоится отдельно              │
│  Контейнеры пересоздаются, raw data остаётся на хосте       │
└─────────────────────────────────────────────────────────────┘
```

**Raw data path:** `orchestrator/storage` в коде — это каталог, куда worker пишет scraped HTML/JSON. Мы монтируем host `data/raw` в этот путь. Один и тот же каталог, разница только в именовании (хост vs контейнер).

### Network Isolation (Dedicated IP)

```
┌────────────────────────────────────────────────────────────┐
│                     Single Server                          │
│                                                            │
│  eth0: 192.168.1.10   (общий)                             │
│  eth0:1 10.0.0.1      (taxlien-parser prod) ← BIND_IP     │
│  eth0:2 10.0.0.2      (taxlien-parser dev)  ← BIND_IP     │
│                                                            │
│  Или: docker0 bridge с отдельной подсетью                  │
│  Или: macvlan для изоляции                                 │
│                                                            │
│  Сервисы слушают только на BIND_IP, не на 0.0.0.0         │
└────────────────────────────────────────────────────────────┘
```

### Deploy Flow

```
Push to branch (prod/dev/stage)
         │
         ▼
┌─────────────────────────────┐
│ GitHub Actions Triggered    │
│ - Select runner by label    │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Checkout code               │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Copy to deploy dir          │
│ Preserve .env, override     │
│ Ensure data/ dirs exist     │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Build images locally        │
│ docker-compose build        │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Restart services            │
│ docker-compose down         │
│ docker-compose up -d        │
└─────────────┬───────────────┘
              │
              ▼
┌─────────────────────────────┐
│ Health check (optional)     │
└─────────────────────────────┘
```

## Interfaces

### Parameterized docker-compose.yml

```yaml
services:
  parser-worker:
    build: .
    image: taxlien-parser-worker:${ENV_TAG:-latest}
    environment:
      - GATEWAY_URL=${GATEWAY_URL}
      - TOR_PROXY_HOST=tor-proxy
      - TOR_PROXY_PORT=${TOR_PORT:-9050}
    volumes:
      - ${DATA_DIR}/raw:/app/orchestrator/storage
    depends_on:
      - tor-proxy
    restart: unless-stopped

  tor-proxy:
    image: wernight/dante
    ports:
      - "${BIND_IP:-0.0.0.0}:${TOR_PORT:-9050}:1080"
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
    ports:
      - "${BIND_IP:-0.0.0.0}:${PROMETHEUS_PORT:-9090}:9090"
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "${BIND_IP:-0.0.0.0}:${GRAFANA_PORT:-3000}:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
    restart: unless-stopped

  cadvisor:
    profiles: ["linux"]
    image: gcr.io/cadvisor/cadvisor:latest
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:rw
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
    ports:
      - "${BIND_IP:-0.0.0.0}:${CADVISOR_PORT:-8080}:8080"
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
```

**Примечания:**
- `BIND_IP` обязателен. macOS: `127.0.0.1`. Linux: выделенный IP.
- `GATEWAY_URL` — URL внешнего Gateway (деплоится отдельно).
- cadvisor — profile `linux`, на macOS не запускается.

### .env.example

```bash
# ===========================================
# Environment Configuration for taxlien-parser
# ===========================================

# --- Core Settings ---
COMPOSE_PROJECT_NAME=taxlien-parser-dev
ENV_TAG=dev

# --- Gateway (отдельный сервис) ---
GATEWAY_URL=http://api.taxlien.online
WORKER_TOKEN=your-worker-token

# --- Network Binding (ОБЯЗАТЕЛЬНО) ---
# macOS: 127.0.0.1
# Linux: выделенный IP (10.0.0.1, 10.0.0.2)
BIND_IP=0.0.0.0

# --- Paths (External Volumes) ---
DATA_DIR=./data

# --- Ports ---
TOR_PORT=9050
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000
CADVISOR_PORT=8080

# --- Grafana ---
GRAFANA_PASSWORD=admin

# ===========================================
# Example: Linux prod
#   BIND_IP=10.0.0.1
#   DATA_DIR=/opt/taxlien-parser/prod/data
#
# Example: macOS stage
#   BIND_IP=127.0.0.1
#   DATA_DIR=~/taxlien-parser/stage/data
# ===========================================
```

### GitHub Actions Workflow

```yaml
name: Deploy

on:
  push:
    branches: [prod, dev, stage]
  workflow_dispatch:
    inputs:
      environment:
        description: 'Environment to deploy'
        required: true
        type: choice
        options: [prod, dev, stage]

jobs:
  deploy:
    runs-on: [self-hosted, "${{ github.ref_name }}"]

    steps:
      - uses: actions/checkout@v4

      - name: Validate environment
        run: |
          if [ -z "${DEPLOY_DIR}" ]; then
            echo "::error::DEPLOY_DIR not set in runner environment"
            exit 1
          fi
          ENV_NAME="${{ github.ref_name }}"
          TARGET_DIR="${DEPLOY_DIR}/${ENV_NAME}"
          DATA_DIR="${TARGET_DIR}/data"
          if [ ! -f "${TARGET_DIR}/.env" ]; then
            echo "::error::.env not found in ${TARGET_DIR}"
            exit 1
          fi
          mkdir -p "${DATA_DIR}"/raw
          echo "DEPLOY_DIR=${DEPLOY_DIR}" >> $GITHUB_ENV
          echo "TARGET_DIR=${TARGET_DIR}" >> $GITHUB_ENV
          echo "DATA_DIR=${DATA_DIR}" >> $GITHUB_ENV

      - name: Deploy
        run: |
          cd "${TARGET_DIR}"
          cp "${GITHUB_WORKSPACE}"/docker-compose.yml . 2>/dev/null || true
          # Copy other needed files...

          # macOS vs Linux path handling
          if [[ "$OSTYPE" == "darwin"* ]]; then
            export DATA_DIR="${TARGET_DIR}/data"
          fi

          # Linux: cadvisor, macOS: без cadvisor
          if [[ "$OSTYPE" == "linux-gnu"* ]]; then
            PROFILE="--profile linux"
          else
            PROFILE=""
          fi
          docker-compose build
          docker-compose down
          docker-compose ${PROFILE} up -d

      - name: Health check
        run: |
          sleep 10
          docker-compose -f "${TARGET_DIR}/docker-compose.yml" ps
```

## Directory Structure on Server

**Linux:**
```
/opt/taxlien-parser/
├── prod/
│   ├── .env
│   ├── docker-compose.yml
│   ├── docker-compose.override.yml
│   └── data/
│       └── raw/
├── dev/
│   └── ...
└── stage/
    └── ...
```

**macOS:**
```
~/taxlien-parser/
├── stage/
│   ├── .env                 # BIND_IP=127.0.0.1
│   ├── docker-compose.yml
│   ├── docker-compose.override.yml
│   └── data/
│       └── raw/
└── dev/
    └── ...
```

## Behavior Specifications

### Happy Path: Push to Branch

1. Developer pushes to `dev` branch
2. GitHub Actions triggers deploy workflow
3. Job runs on runner with label `dev`
4. Runner checks out code
5. Files copied to deploy dir (preserving .env, override, data/)
6. `docker-compose build` builds images with tag `:dev`
7. `docker-compose down` stops current containers
8. `docker-compose up -d` starts new containers
9. Health check verifies containers
10. Workflow completes

### Edge Cases

| Case | Expected Behavior |
|------|-------------------|
| Missing .env | Workflow fails with clear error |
| Build failure | Old containers keep running |
| Port conflict | docker-compose up fails |
| Disk full | Build fails |
| macOS runner | Uses DEPLOY_DIR=~/taxlien-parser, BIND_IP=127.0.0.1 |

## Migration / Rollout

### Initial Setup per Server

#### Linux

1. Install Docker Engine, Docker Compose
2. Install GitHub Runner with label (prod/dev/stage)
3. Set `export DEPLOY_DIR=/opt/taxlien-parser` in runner env
4. Create dirs: `mkdir -p /opt/taxlien-parser/{prod,dev,stage}/data/raw`
5. Copy `.env.example` → `.env` in each env dir, set BIND_IP, DATA_DIR

#### macOS

1. Install Docker Desktop
2. Install GitHub Runner with label (stage)
3. Set `export DEPLOY_DIR=~/taxlien-parser`
4. Create dirs: `mkdir -p ~/taxlien-parser/{stage,dev}/data/raw`
5. Copy `.env.example` → `.env`, set `BIND_IP=127.0.0.1`, `DATA_DIR=./data`

## Resolved

- [x] Gateway — деплоится отдельно, GATEWAY_URL в .env
- [x] Мониторинг — prometheus, grafana, cadvisor в CI/CD
- [x] Raw path — `data/raw` (host) = `orchestrator/storage` (container)

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
