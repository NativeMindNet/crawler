# Implementation Plan: Tax Lien Parser CI/CD

> Version: 1.0
> Status: DRAFT
> Last Updated: 2026-02-12
> Specifications: ./02-specifications.md

## Summary

Реализация CI/CD для автодеплоя taxlien-parser на prod/dev/stage инстансы с поддержкой Linux и macOS. Ключевые deliverable: параметризованный docker-compose.yml с external volumes, .env.example, GitHub Actions workflow.

## Task Breakdown

### Phase 1: Docker Compose for CI/CD

#### Task 1.1: Создание docker-compose.yml для деплоя
- **Description**: Создать/адаптировать docker-compose с параметризацией
- **Files**: `docker-compose.yml` (или отдельный `docker-compose.deploy.yml`)
- **Dependencies**: None
- **Verification**: `docker-compose config` без ошибок
- **Complexity**: Medium

**Changes:**
- BIND_IP, *_PORT переменные
- ENV_TAG для образов
- External volumes: `${DATA_DIR}/postgres`, `${DATA_DIR}/redis`, `${DATA_DIR}/raw`
- COMPOSE_PROJECT_NAME через .env

#### Task 1.2: External volumes (bind mount)
- **Description**: Настроить bind mount для raw data (orchestrator/storage) на хосте
- **Files**: `docker-compose.yml`
- **Dependencies**: Task 1.1
- **Verification**: После пересоздания контейнеров данные сохраняются
- **Complexity**: Low

```yaml
volumes:
  - ${DATA_DIR}/raw:/app/orchestrator/storage
```

#### Task 1.3: Мониторинг (prometheus, grafana, cadvisor)
- **Description**: Добавить сервисы мониторинга, cadvisor с profile linux
- **Files**: `docker-compose.yml`, `monitoring/`
- **Dependencies**: Task 1.1
- **Verification**: Grafana доступна, prometheus собирает метрики
- **Complexity**: Medium

#### Task 1.4: Параметризация портов и IP
- **Description**: Все порты и BIND_IP через переменные
- **Files**: `docker-compose.yml`
- **Dependencies**: Task 1.1
- **Verification**: Запуск с разными .env — разные порты/IP
- **Complexity**: Low

### Phase 2: Environment Configuration

#### Task 2.1: Создание .env.example
- **Description**: Шаблон переменных с документацией
- **Files**: `.env.example`
- **Dependencies**: Phase 1 complete
- **Verification**: Копия как .env позволяет запустить
- **Complexity**: Low

**Содержание:**
- COMPOSE_PROJECT_NAME, ENV_TAG
- GATEWAY_URL, WORKER_TOKEN (gateway отдельно)
- BIND_IP (обязательно)
- DATA_DIR
- TOR_PORT, PROMETHEUS_PORT, GRAFANA_PORT, CADVISOR_PORT
- GRAFANA_PASSWORD
- Примеры для Linux и macOS

#### Task 2.2: Обновление .gitignore
- **Description**: Добавить .env в .gitignore
- **Files**: `.gitignore`
- **Dependencies**: None
- **Verification**: `git status` не показывает .env

### Phase 3: GitHub Actions Workflow

#### Task 3.1: Создание deploy workflow
- **Description**: deploy.yml с triggers
- **Files**: `.github/workflows/deploy.yml`
- **Dependencies**: None
- **Verification**: Workflow в GitHub Actions UI
- **Complexity**: Medium

**Structure:**
- on: push branches [prod, dev, stage], workflow_dispatch
- runs-on: [self-hosted, env_name]

#### Task 3.2: Environment validation
- **Description**: Проверка DEPLOY_DIR, .env, создание data dirs
- **Files**: `.github/workflows/deploy.yml`
- **Dependencies**: Task 3.1
- **Verification**: Fail если .env отсутствует
- **Complexity**: Low

#### Task 3.3: Deploy step с multi-platform
- **Description**: Copy files, build, restart. macOS vs Linux paths
- **Files**: `.github/workflows/deploy.yml`
- **Dependencies**: Task 3.2
- **Verification**: Работает на macOS и Linux runner
- **Complexity**: Medium

#### Task 3.4: Health check step
- **Description**: Проверка контейнеров (warning only)
- **Files**: `.github/workflows/deploy.yml`
- **Dependencies**: Task 3.3
- **Verification**: Warning при < N running
- **Complexity**: Low

### Phase 4: Documentation

#### Task 4.1: README CI/CD section
- **Description**: Инструкции по настройке runner'ов и деплою
- **Files**: `README.md` или `docs/CI-CD.md`
- **Dependencies**: All previous
- **Verification**: Понятно как настроить новый инстанс

#### Task 4.2: Локальное тестирование
- **Description**: Проверка docker-compose локально (macOS/Linux)
- **Files**: None
- **Verification**:
  - `docker-compose config` без ошибок
  - `docker-compose up -d` с .env
  - Данные в data/ после перезапуска

## Dependency Graph

```
Phase 1                         Phase 2              Phase 3
Task 1.1 ──┬──→ Task 1.2        Task 2.1             Task 3.1
           ├──→ Task 1.3        (.env.example)          │
           └──→ Task 1.4             │                  ▼
                                     │              Task 3.2
           Task 2.2             │                  │
           (.gitignore)         │                  ▼
                                │              Task 3.3
                                │                  │
                                │                  ▼
                                │              Task 3.4
                                │                  │
                                ▼                  ▼
                           ┌─────────────────────────────┐
                           │  Phase 4: Docs & Testing    │
                           └─────────────────────────────┘
```

## File Change Summary

| File | Action | Reason |
|------|--------|--------|
| `docker-compose.yml` | Create/Modify | Параметризация, external volumes |
| `docker-compose.dev.yml` | Possibly merge | База для dev |
| `.env.example` | Create | Шаблон конфигурации |
| `.github/workflows/deploy.yml` | Create | CI/CD workflow |
| `.gitignore` | Modify | .env |
| `README.md` или `docs/CI-CD.md` | Modify/Create | Документация |

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| GATEWAY_URL недоступен | Medium | High | Health check, документация |
| Permissions на data/raw | Medium | Medium | chown в setup инструкции |
| macOS vs Linux (cadvisor) | Low | Low | profile linux |

## Checkpoints

### После Phase 1:
- [ ] docker-compose config без ошибок
- [ ] External volume (raw) настроен
- [ ] Мониторинг (prometheus, grafana, cadvisor) добавлен
- [ ] BIND_IP применяется

### После Phase 2:
- [ ] .env.example полный
- [ ] .env в .gitignore

### После Phase 3:
- [ ] Workflow в GitHub UI
- [ ] Push в dev триггерит

### После Phase 4:
- [ ] README обновлен
- [ ] Локальный тест пройден

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
