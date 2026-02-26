# Implementation Plan: Local Storage & Synchronization for Tax Lien Parser

## Phase 1: Database Layer
1.  **Dependency**: Add `aiosqlite` to `requirements.txt`.
2.  **Implementation**: Create `storage/db.py`.
    - Setup connection management.
    - Implement `init()` with table creation (tasks and local_results).
    - Implement CRUD operations.
3.  **Test**: Create unit test `tests/unit/test_storage.py` to verify DB ops.

## Phase 2: Worker Integration
1.  **Runner Update**: Modify `worker/runner.py` to initialize DB on startup.
2.  **Save Logic**: Inject `db.save_result` into `_process_task`.
3.  **Error Handling**: Ensure scraping continues even if DB or API fails.

## Phase 3: Synchronization Mechanism
1.  **Sync Manager**: Create `storage/sync.py`.
    - Periodic check for unsynced rows.
    - Exponential backoff logic.
2.  **Loop Integration**: Add `_sync_loop` to `WorkerRunner`.
3.  **Batching**: Implement batch submission in `SyncManager` if many rows are pending.

## Phase 4: Verification & Polishing
1.  **Integration Test**: Create test scenario where Gateway is mocked to fail initially then succeed.
2.  **Logging**: Ensure clear visibility into what's synced and what's pending.
3.  **Documentation**: Update README with info about local persistence.

## Task Breakdown
| Task | Description | Status |
| :--- | :--- | :--- |
| 1.1 | Add `aiosqlite` to requirements | TODO |
| 1.2 | Implement `storage/db.py` | TODO |
| 2.1 | Modify `WorkerRunner` to use DB | TODO |
| 3.1 | Implement `SyncManager` loop | TODO |
| 4.1 | Verify with mock failures | TODO |