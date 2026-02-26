# Requirements: Tax Lien Parser CI/CD

> Version: 1.0
> Status: DRAFT
> Last Updated: 2026-02-12

## Problem Statement

Необходимо автоматизировать процесс деплоя **taxlien-parser** на различные окружения (prod, dev, stage) при пуше в соответствующие ветки.

**Ключевые проблемы текущей конфигурации:**
- Порты захардкожены — невозможно запустить несколько окружений на одном сервере
- Нет привязки к конкретному IP — сервисы слушают на 0.0.0.0, конфликты с другими Docker-проектами
- Образы без тегов окружения — конфликты при нескольких средах
- БД и raw data внутри контейнеров — данные теряются при пересоздании, нет персистентности на хосте

## Current State

**Репозиторий:** taxlien-parser

**Сервисы в docker-compose:**
| Сервис | Порт | Build | Описание |
|--------|------|-------|----------|
| parser-worker | - | ./Dockerfile | Python worker (scraper/parser) |
| tor-proxy | 9050 | image: wernight/dante | SOCKS proxy (mock/dev) |
| prometheus | 9090 | image: prom/prometheus | Метрики парсера |
| grafana | 3000 | image: grafana/grafana | Дашборды |
| cadvisor | 8080 | image: gcr.io/cadvisor | Container metrics (Linux only) |

**Gateway** деплоится отдельно (свой репо/CI). Parser подключается к нему через `GATEWAY_URL` в .env.

**Структура:**
```
taxlien-parser/
├── docker-compose.dev.yml    # Dev compose
├── Dockerfile                # Parser worker
├── db/                       # Migrations, connection
├── orchestrator/             # Queue, storage
├── platforms/                # Platform configs
├── scrapers/                 # Scraper implementations
├── strategies/               # Task selection
└── worker/                   # Worker entrypoints
```

## User Stories

### Primary

**As a** разработчик
**I want** автоматический деплой при пуше в ветку (prod/dev/stage)
**So that** я могу быстро доставлять изменения без ручных операций

**As a** DevOps инженер
**I want** БД и raw data в external volumes (bind mount на хост)
**So that** данные сохраняются при пересоздании контейнеров и доступны для бэкапов

**As a** оператор
**I want** Docker с отдельным IP/интерфейсом для taxlien-parser
**So that** не было накладок с другими Docker-проектами на том же сервере

**As a** оператор
**I want** запуск dev и prod (и stage) на одном сервере без конфликтов
**So that** эффективнее использовать ресурсы

### Secondary

**As a** разработчик
**I want** возможность запуска stage на macOS
**So that** локальная отладка и тесты на Mac перед деплоем на Linux

## Acceptance Criteria

### Must Have

1. **Given** пуш в ветку `prod`/`dev`/`stage`
   **When** GitHub Actions workflow запускается
   **Then** self-hosted runner на соответствующем инстансе:
   - Собирает образы локально
   - Обновляет и перезапускает контейнеры
   - Все сервисы деплоятся вместе

2. **Given** dev и prod на одном сервере
   **When** оба окружения запущены
   **Then** они используют:
   - Разные IP-адреса/интерфейсы (отдельный BIND_IP для каждого env)
   - Разные теги образов (`:dev`, `:prod`, `:stage`)
   - Изолированные volumes по окружениям
   - Не конфликтуют по портам

3. **Given** raw data (scraped HTML/JSON)
   **When** контейнеры пересоздаются
   **Then** данные хранятся в external volume: `${DATA_DIR}/raw` → `orchestrator/storage`

4. **Given** Docker на сервере с несколькими проектами
   **When** taxlien-parser запущен
   **Then** сервисы привязаны к выделенному IP (BIND_IP), не слушают 0.0.0.0

5. **Given** stage окружение на macOS
   **When** workflow выполняется на macOS runner
   **Then** деплой работает (DEPLOY_DIR, paths адаптированы под macOS)

6. **Given** деплой на инстанс
   **When** обновляется docker-compose из репо
   **Then** локальные `.env` и `docker-compose.override.yml` сохраняются

7. **Given** новый инстанс настраивается
   **When** оператор смотрит репозиторий
   **Then** есть `.env.example` с документацией всех переменных

### Should Have

- Ручной триггер workflow (workflow_dispatch)
- Простой health check после деплоя
- Логи вынесены из контейнера через volume (опционально)

### Won't Have (This Iteration)

- Blue-green deployment
- Автоматический rollback
- Уведомления (Slack/Telegram)
- Kubernetes

## Technical Decisions

### Хранение данных (External Volumes)

- **Подход:** bind mount на хост через `${DATA_DIR}`
- **Структура на хосте:**
  ```
  ${DATA_DIR}/
  └── raw/          # Raw scraped files (HTML, JSON) → orchestrator/storage
  ```
- **Raw data path:** Хост `data/raw` монтируется в `orchestrator/storage` внутри контейнера. Это один и тот же каталог — в коде worker пишет в `orchestrator/storage`, мы просто выносим его на хост для персистентности.
- **Платформы:** Linux — `/opt/taxlien-parser/{env}/data/`, macOS — `~/taxlien-parser/{env}/data/`

### Конфигурация

- **Подход:** `.env` + `docker-compose.override.yml` на сервере
- **Расположение:** `${DEPLOY_DIR}/{env}/`
- **Что обновляется при деплое:** только `docker-compose.yml` и артефакты из репо
- **Что сохраняется:** `.env`, `docker-compose.override.yml`, `data/`

### Сеть

- **BIND_IP:** обязательная переменная для привязки сервисов к конкретному IP
- **На macOS:** обычно `127.0.0.1` (localhost)
- **На Linux:** выделенный IP интерфейса (например `10.0.0.1` для prod, `10.0.0.2` для dev)

## Constraints

- **Infrastructure:** Self-hosted GitHub Runner на каждом инстансе
- **Platform:** Docker + docker-compose на Linux и macOS (stage)
- **Network:** Разные IP-адреса для разных окружений на Linux
- **Data:** External volume (bind mount) для raw/orchestrator storage
- **Build:** Сборка образов происходит локально на runner'е

## Resolved

- [x] **Gateway** — деплоится отдельно (свой репо/CI). Parser использует `GATEWAY_URL` для подключения.
- [x] **Мониторинг** — да, cadvisor + prometheus + grafana входят в этот CI/CD.
- [x] **Raw data path** — `data/raw` на хосте = `orchestrator/storage` в контейнере (один каталог, mount).

## References

- [GitHub Actions self-hosted runners](https://docs.github.com/en/actions/hosting-your-own-runners)
- [Docker Compose environment variables](https://docs.docker.com/compose/environment-variables/)
- [taxlien-parser architecture](sdd-taxlien-parser-architecture/01-architecture.md)

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions]
