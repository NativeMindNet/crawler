# Plan: Delinquency-Based Priority Implementation

> Version: 0.1  
> Status: DRAFT  
> Last Updated: 2026-02-04  
> Specifications: [02-specifications.md](02-specifications.md)

---

## 1. Overview
This plan implements the "Risk-Based Priority" system. It focuses on identifying and prioritizing delinquent parcels, multiple-lien properties (stacking), and the upcoming Arizona Feb 2026 auction.

## 2. Atomic Tasks

### Task 1: Create `RiskBasedStrategy`
- **File:** `strategies/implementations/risk.py`
- **Goal:** Create a new selection strategy that favors distressed properties.
- **Logic:**
    - Query `tasks` WHERE `tags` contains 'delinquent', 'stacking', or 'auction_feb_2026'.
    - ORDER BY `priority` DESC.
    - Fallback to high-priority tasks generally if no tagged tasks exist.

### Task 2: Implement Signal Detection in LPM
- **File:** `storage/db.py`
- **Goal:** Detect "Risk Signals" from scraped data and persist them to the task record.
- **Modifications:**
    - In `save_result()`, analyze the `result.data` object.
    - Check for `total_due > 0` (delinquent).
    - Check for `len(liens) > 1` (stacking).
    - If detected, perform an `UPDATE tasks SET priority = 200, tags = tags || ',delinquent' ...`.

### Task 3: Arizona Feb 2026 Boost
- **File:** `storage/db.py`
- **Goal:** Ensure all AZ tasks get immediate attention before Feb 28, 2026.
- **Modifications:**
    - In `register_task()`, if `state == 'AZ'`, set `priority = 150` and add `auction_feb_2026` tag.

### Task 4: Integrate into Strategy Mixer
- **File:** `storage/db.py`
- **Goal:** Activate the new strategy in the worker.
- **Modifications:**
    - In `_init_mixer()`, add `RiskBasedStrategy` to the strategies list.
    - Set weights: `{"risk": 0.5, "chronos": 0.3, "ripple": 0.2}`.

---

## 3. Verification Plan

### 3.1 Unit Tests
- Create `tests/strategies/test_risk_strategy.py`.
- Verify that `RiskBasedStrategy` returns tasks with specific tags first.
- Verify that `Priority 255` still takes precedence (Global Hotspot).

### 3.2 Integration Tests
- Run a dummy scrape where the parser returns "delinquent" data.
- Verify the task is updated in `worker_state.db` with the correct tags and boosted priority.

---

## 4. Complexity Estimate
- **RiskBasedStrategy:** Small
- **Signal Detection:** Medium (data parsing logic)
- **Mixer Integration:** Small
- **Total:** ~2-3 hours of implementation.
