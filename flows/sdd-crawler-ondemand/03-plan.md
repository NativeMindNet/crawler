# Implementation Plan: On-demand Mode (Decoupled)

> Version: 0.1  
> Status: DRAFT  
> Last Updated: 2026-01-30  
> Specifications: [02-specifications.md](02-specifications.md)

## 1. Summary

Implement the `OndemandRunner` which manages three concurrent `asyncio` loops. This runner relies on the `LocalPersistenceManager` (from the `localstorage` flow) for all state management.

## 2. Task Breakdown

### Phase 1: Skeleton & Orchestration

#### Task 1.1: Create OndemandRunner Skeleton
- **Description**: Define the `OndemandRunner` class in `worker/runner_ondemand.py` with placeholders for the three loops.
- **Files**: `worker/runner_ondemand.py` (New)
- **Dependencies**: None
- **Complexity**: Low

#### Task 1.2: Update main.py for Mode Selection
- **Description**: Add `--mode` argument to `main.py`. Support `legacy` (current) and `ondemand`.
- **Files**: `main.py`
- **Dependencies**: Task 1.1
- **Complexity**: Low

### Phase 2: The Collector Loop (PULL)

#### Task 2.1: Implement Collector Logic
- **Description**: Loop that calls `gateway.get_work()` and saves tasks to LPM with status `pending`.
- **Files**: `worker/runner_ondemand.py`
- **Dependencies**: `LocalPersistenceManager`
- **Verification**: Mock Gateway response and check SQLite `tasks` table.
- **Complexity**: Medium

### Phase 3: The Executor Loop (PROCESS)

#### Task 3.1: Implement Executor Logic
- **Description**: Loop that picks `pending` tasks from LPM, runs scrapers via `ScraperFactory`, and saves results to LPM.
- **Files**: `worker/runner_ondemand.py`
- **Dependencies**: Task 1.1, `LocalPersistenceManager`
- **Verification**: Run with a sample task in DB and verify result is saved.
- **Complexity**: Medium

### Phase 4: The Sync Loop (PUSH)

#### Task 4.1: Implement Result Sync Logic
- **Description**: Loop that finds `unsynced` results in LPM and calls `gateway.submit_results()`.
- **Files**: `worker/runner_ondemand.py`
- **Dependencies**: Task 1.1
- **Verification**: Check Gateway logs for received results after local completion.
- **Complexity**: Medium

#### Task 4.2: Implement Raw File Sync Logic
- **Description**: Ensure raw HTML files are uploaded before or alongside JSON results.
- **Files**: `worker/runner_ondemand.py`
- **Complexity**: Medium

### Phase 5: Reliability & Recovery

#### Task 5.1: Startup Recovery Logic
- **Description**: On startup, move any tasks in `processing` state back to `pending`.
- **Files**: `worker/runner_ondemand.py`
- **Complexity**: Low

## 3. File Change Summary

| File | Action | Reason |
|------|--------|--------|
| `worker/runner_ondemand.py` | Create | New decoupled runner implementation. |
| `main.py` | Modify | Entry point for the new mode. |
| `client/gateway.py` | Modify | Add any missing helper methods for batch sync. |

## 4. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Database contention (SQLite locks) | Use a single write connection or WAL mode in LPM. |
| Gateway overload during sync | Implement exponential backoff in the Sync Loop. |
| LPM implementation delays | Mock the `LocalPersistenceManager` interface if needed for testing `OndemandRunner`. |
