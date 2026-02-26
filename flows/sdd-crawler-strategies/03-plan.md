# Plan: Traversal Strategy Module Implementation

> Version: 0.1  
> Status: DRAFT  
> Last Updated: 2026-02-04  
> Specifications: [02-specifications.md](02-specifications.md)

---

## Phase 1: Core Foundation (The "Brain" Skeleton)

### Task 1.1: Project Structure Setup
- **Goal:** Create the directory structure for the module.
- **Files:** `taxlien_parser/strategy/__init__.py`, `taxlien_parser/strategy/models.py`.
- **Action:** Define the `Task` dataclass and basic types.

### Task 1.2: Base Strategy Interface
- **Goal:** Implement the abstract base class.
- **Files:** `taxlien_parser/strategy/base.py`.
- **Details:** Define `BaseStrategy` with `suggest_tasks(limit)` and `feedback()`.

### Task 1.3: Strategy Mixer (Scheduler)
- **Goal:** Implement the weighted selection logic.
- **Files:** `taxlien_parser/strategy/mixer.py`.
- **Details:** Implement `StrategyMixer` that accepts a dict of strategies and weights. Implement simple random weighted choice first.

## Phase 2: Standard Strategies Implementation

### Task 2.1: Chronos Strategy (Freshness)
- **Goal:** Implement the "Oldest First" logic.
- **Files:** `taxlien_parser/strategy/strategies/chronos.py`.
- **Action:** Write SQL query `ORDER BY last_scraped_at ASC`. Integration with a mock DB connector.

### Task 2.2: Targeted Strategy (Auction)
- **Goal:** Implement filtering by tags/dates.
- **Files:** `taxlien_parser/strategy/strategies/targeted.py`.
- **Action:** Logic to filter by `auction_date` or `state`.

### Task 2.3: Sweeper Strategy (Linear)
- **Goal:** Implement range-based discovery.
- **Files:** `taxlien_parser/strategy/strategies/sweeper.py`.
- **Action:** Logic to store `current_id` state and increment.

## Phase 3: The Hotspot System (User Signals)

### Task 3.1: Signal Model & Storage
- **Goal:** Define the `UserSignal` schema.
- **Files:** `taxlien_parser/storage/schema_updates.sql` (or migration).
- **Action:** Create `user_signals` table.

### Task 3.2: Hotspot Strategy Logic
- **Goal:** Implement the strategy that reads signals.
- **Files:** `taxlien_parser/strategy/strategies/hotspot.py`.
- **Action:** Query that joins `tasks` with `user_signals`.

## Phase 4: Integration & Testing

### Task 4.1: LPM Integration Mock
- **Goal:** Create a fake LPM to test strategies in isolation.
- **Files:** `tests/mocks/mock_lpm.py`.

### Task 4.2: Mixer Unit Tests
- **Goal:** Verify that 70/30 split actually works.
- **Files:** `tests/strategy/test_mixer.py`.

### Task 4.3: Starvation Protection Logic
- **Goal:** Refine Mixer to ensure low-priority strategies get run.
- **Files:** `taxlien_parser/strategy/mixer.py` (Update).

## Phase 5: Client Usage Example

### Task 5.1: API Signal Injection Example
- **Goal:** Show how the API will use this system.
- **Files:** `examples/api_signal_demo.py`.
