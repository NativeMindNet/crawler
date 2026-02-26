# Implementation Log: On-demand Mode (Gateway-Driven)

> Started: 2026-01-30  
> Plan: [03-plan.md](03-plan.md)

## Progress Tracker

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1: Skeleton & Orchestration | Done | Merged into WorkerRunner |
| Phase 2: Collector Loop | Done | _gateway_pull_loop |
| Phase 3: Executor Loop | Done | Main loop fetches from LPM |
| Phase 4: Sync Loop | Done | SyncService |
| Phase 5: Recovery | Pending | |

## Session Log

### Session 2026-01-30

**Completed:**
- Task 1.1: Decoupled logic integrated into `WorkerRunner` (unified architecture for standalone + on-demand)
- Task 2.1: `WorkerRunner._gateway_pull_loop` acts as Collector
- Task 3.1: Main loop acts as Executor (fetching from LPM)
- Task 4.1: `WorkerRunner._sync_loop` using `SyncService` acts as Pusher
- `LocalPersistenceManager` updated with `get_next_task` and `fail_task`

#### Deviations from Plan
- No separate `OndemandRunner` — integrated into existing `WorkerRunner` for simpler architecture.

## Completion Checklist

- [x] Phase 1-4 core logic complete
- [ ] Phase 5: Startup recovery
- [ ] Full integration testing
