# Plan: Standalone Mode Implementation

**Version:** 0.1
**Status:** PLAN PHASE
**Last Updated:** 2026-01-30

---

## Phase 1: Local Client Infrastructure

- [ ] **Task 1.1: Create `client/local.py`**
    - Implement `LocalClient` class with `GatewayClient` compatible interface.
    - Implement `get_work` reading from JSON.
    - Implement `submit_results` writing to JSON files in `./output`.
    - Implement `upload_raw_file` saving HTML to disk.
- [ ] **Task 1.2: Implement Resume Logic**
    - Add `.resume` file support to `LocalClient`.
- [ ] **Task 1.3: Add JSON Task Schema Validation** (Optional but recommended).

## Phase 2: Worker Refactoring

- [ ] **Task 2.1: Refactor `WorkerRunner` for Heartbeat Optionality**
    - Make heartbeat loop conditional (only if using `GatewayClient`).
    - Ensure `_process_task` works seamlessly with `LocalClient`.
- [ ] **Task 2.2: Add Standalone Exit Condition**
    - In standalone mode, `WorkerRunner` should stop when `get_work()` returns empty list.

## Phase 3: CLI & Entry Point

- [ ] **Task 3.1: Update `main.py` Arguments**
    - Add `--standalone`, `--input`, `--parcel`, `--output-dir`.
- [ ] **Task 3.2: Implement Factory for Client Selection**
    - Logic to instantiate `GatewayClient` or `LocalClient` based on flags.

## Phase 4: Verification & Testing

- [ ] **Task 4.1: Manual Test with Single Parcel**
    - Run: `python main.py --standalone --platform floridatax --parcel 123 --state FL --county Clay`.
- [ ] **Task 4.2: Manual Test with Input File**
    - Create `tasks.json`.
    - Run: `python main.py --standalone --input tasks.json --resume`.
    - Verify results in `./output`.
- [ ] **Task 4.3: Verify Raw HTML Storage**
    - Check if `.html.gz` files are created correctly.

---

## Dependencies
- Existing `Task` and `ParcelResult` models in `client/gateway.py`.
- `ScraperFactory` and `ParserRegistry`.
