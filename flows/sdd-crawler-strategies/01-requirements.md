# Requirements: Traversal Strategy Module

**Version:** 0.3
**Status:** REQUIREMENTS PHASE
**Last Updated:** 2026-01-31

---

## 1. Goal
Decouple the task selection logic from the worker and storage layers. The module acts as the "Brain", selecting the most impactful tasks based on configuration, data hygiene (freshness), and user signals.

## 2. User Stories

### US-1: Strategy Mixing & Starvation Protection
**As a** system operator  
**I want** to ensure that "Freshness" updates (Chronos) always get at least 10% of resources, even during high-priority auctions
**So that** the database doesn't develop blind spots or "rot" completely.

### US-2: User Interest Driven (Hotspot)
**As a** user
**I want** the system to prioritize parsing counties I am currently viewing on the map
**So that** I get the freshest data for my active research area without manually clicking "Update".

### US-3: Discovery vs Update
**As a** researcher
**I want** to switch between "Sweeping" (finding hidden records) and "Enrichment" (updating known IDs)
**So that** I can choose between expanding coverage or keeping data fresh.

## 3. Functional Requirements

### FR-1: Unified Strategy Interface
- Method: `suggest_tasks(db_connection, limit) -> List[Task]`.

### FR-2: The Strategy Mixer (Weighted Scheduler)
- Manages active strategies and their weights.
- **Critical:** Must support `min_guaranteed_capacity` for low-priority strategies to prevent starvation.

### FR-3: Standard Strategies List

#### A. Chronos Strategy (Freshness / Maintenance)
- **Logic:** `ORDER BY last_scraped_at ASC NULLS FIRST`.
- **Goal:** Eliminates blind spots. Updates oldest records and never-scraped tasks.
- **Role:** Background maintenance.

#### B. Hotspot Strategy (User Signals)
- **Logic:** Prioritizes regions or entities found in `user_interests` table/log.
- **Input:** Receives "Signals" from the Ecosystem (e.g., "User viewing Miami-Dade").
- **Goal:** Reactive updates based on actual demand. Replaces synchronous OnDemand calls.

#### C. Targeted Strategy (Business / Auction)
- **Logic:** Filters by specific tags (e.g., `auction_date` within 30 days).
- **Goal:** Business deadlines.

#### D. Ripple Strategy (Graph / Context)
- **Logic:** Follows relations (Neighbors, Owner Portfolios).
- **Trigger:** Activation of a "High Value" node.

#### E. Sweeper Strategy (Linear / Blind)
- **Logic:** Sequential iteration (`ID > max_id`).
- **Goal:** Pure discovery of unindexed records.

#### F. Seeded Strategy (Dictionary)
- **Logic:** Search by known keywords/names.

## 4. Non-Functional Requirements
- **Performance:** Selection < 500ms.
- **Throttle Safety:** Hotspot strategy must respect site rate limits even if user demand is high (Queue-based, not Request-based).

## 5. Architecture Notes
- **LPM Integration:** Strategies query LPM.
- **Signal Ingestion:** A mechanism to feed `user_interests` (Region, ParcelID, PartyID) into LPM for the Hotspot Strategy to read.