# Specifications: On-demand Mode (Gateway-Driven)

> Version: 0.2  
> Status: DRAFT  
> Last Updated: 2026-02-04  
> Requirements: [01-requirements.md](01-requirements.md)

---

## 1. Priority-Aware Pull
Воркер при запросе `/internal/work` получает задачи, приоритет которых уже пересчитан на стороне Gateway с учетом Ripple Effect (Incremental Delta).

## 2. Real-time Feedback Loop
1. Воркер отправляет результат в Gateway.
2. Gateway видит `discovered_links`.
3. Gateway применяет дельты к связанным задачам в своей глобальной очереди.
4. При следующем `GET /internal/work` воркер (или другой воркер) получает эти связанные задачи.

## 3. Resilience (Graceful Degradation)
Если Gateway недоступен:
- Воркер продолжает работать, используя задачи из своей локальной SQLite (наполненной ранее).
- Результаты копятся в `localstorage`.
- Как только Gateway оживает, `SyncService` выгружает "волну" накопленных ссылок, и Gateway обновляет свой глобальный граф.
