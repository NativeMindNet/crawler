# Requirements: Traversal Strategy Module (Celery Integration)

**Version:** 1.0
**Status:** DRAFT
**Last Updated:** 2026-03-01

---

## 1. Goal

Decouple task selection logic from execution. Strategies act as the "Brain", selecting high-impact tasks and submitting them to **Celery queues** for distributed execution.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      STRATEGY SYSTEM                                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Celery Beat (Scheduler)                       │   │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │   │
│  │  │run_chronos  │ │run_targeted │ │run_hotspot  │  ...          │   │
│  │  │ (*/5 min)   │ │ (*/1 hour)  │ │ (*/1 min)   │               │   │
│  │  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘               │   │
│  └─────────┼───────────────┼───────────────┼───────────────────────┘   │
│            │               │               │                           │
│            ▼               ▼               ▼                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Strategy Mixer                               │   │
│  │  Weights: Chronos=10% | Targeted=50% | Hotspot=30% | Sweeper=10%│   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Strategy Implementations                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │   │
│  │  │ Chronos  │ │ Targeted │ │ Hotspot  │ │ Sweeper  │  ...      │   │
│  │  │(freshness│ │(auction) │ │ (user)   │ │(discover)│           │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │   │
│  └───────┼────────────┼────────────┼────────────┼─────────────────┘   │
│          │            │            │            │                      │
│          └────────────┴─────┬──────┴────────────┘                      │
│                             │ suggest_tasks()                          │
│                             ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       Redis Broker                               │   │
│  │              Queues: urgent | high | default | low               │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                      Celery Workers                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Strategy Interface

```python
from abc import ABC, abstractmethod
from typing import List
from dataclasses import dataclass

@dataclass
class TaskSuggestion:
    url: str
    priority: int
    queue: str
    metadata: dict

class Strategy(ABC):
    """Base class for all traversal strategies."""

    @abstractmethod
    def suggest_tasks(self, limit: int) -> List[TaskSuggestion]:
        """Return list of tasks to execute."""
        pass

    def execute(self, limit: int = 100):
        """Generate tasks and submit to Celery."""
        suggestions = self.suggest_tasks(limit)

        for task in suggestions:
            scrape_task.apply_async(
                args=[task.url],
                kwargs={'metadata': task.metadata},
                queue=task.queue,
                priority=task.priority
            )

        return len(suggestions)
```

---

## 4. Standard Strategies

### A. Chronos Strategy (Freshness / Maintenance)

**Purpose:** Update oldest records, eliminate blind spots.

```python
class ChronosStrategy(Strategy):
    """Update properties by staleness."""

    def suggest_tasks(self, limit: int) -> List[TaskSuggestion]:
        # Query LPM for oldest records
        properties = lpm.query("""
            SELECT * FROM properties
            WHERE last_scraped_at IS NULL
               OR last_scraped_at < datetime('now', '-7 days')
            ORDER BY last_scraped_at ASC NULLS FIRST
            LIMIT ?
        """, [limit])

        return [
            TaskSuggestion(
                url=p.url,
                priority=3,
                queue='default',
                metadata={'strategy': 'chronos', 'property_id': p.id}
            )
            for p in properties
        ]
```

**Beat Schedule:** Every 5 minutes

---

### B. Targeted Strategy (Business / Auction)

**Purpose:** Focus on auction-imminent properties.

```python
class TargetedStrategy(Strategy):
    """Target properties with upcoming auctions."""

    def __init__(self, days_ahead: int = 30):
        self.days_ahead = days_ahead

    def suggest_tasks(self, limit: int) -> List[TaskSuggestion]:
        properties = lpm.query("""
            SELECT * FROM properties
            WHERE auction_date IS NOT NULL
              AND auction_date <= date('now', '+? days')
              AND (last_scraped_at IS NULL
                   OR last_scraped_at < datetime('now', '-1 day'))
            ORDER BY auction_date ASC
            LIMIT ?
        """, [self.days_ahead, limit])

        return [
            TaskSuggestion(
                url=p.url,
                priority=1,  # Urgent
                queue='urgent',
                metadata={'strategy': 'targeted', 'auction_date': p.auction_date}
            )
            for p in properties
        ]
```

**Beat Schedule:** Every hour

---

### C. Hotspot Strategy (User Signals)

**Purpose:** Prioritize regions users are actively viewing.

```python
class HotspotStrategy(Strategy):
    """React to user interest signals."""

    def suggest_tasks(self, limit: int) -> List[TaskSuggestion]:
        # Get recent user interest signals
        signals = lpm.query("""
            SELECT DISTINCT county, state FROM user_interests
            WHERE created_at > datetime('now', '-10 minutes')
        """)

        if not signals:
            return []

        # Get stale properties in those regions
        properties = lpm.query("""
            SELECT * FROM properties
            WHERE (county, state) IN (SELECT county, state FROM user_interests
                                      WHERE created_at > datetime('now', '-10 minutes'))
              AND (last_scraped_at IS NULL
                   OR last_scraped_at < datetime('now', '-1 hour'))
            ORDER BY last_scraped_at ASC
            LIMIT ?
        """, [limit])

        return [
            TaskSuggestion(
                url=p.url,
                priority=2,
                queue='high',
                metadata={'strategy': 'hotspot', 'county': p.county}
            )
            for p in properties
        ]
```

**Beat Schedule:** Every minute

---

### D. Ripple Strategy (Graph / Context)

**Purpose:** Follow relations from high-value nodes.

```python
class RippleStrategy(Strategy):
    """Explore neighbors of high-value properties."""

    def suggest_tasks(self, limit: int) -> List[TaskSuggestion]:
        # Find recently discovered high-value properties
        high_value = lpm.query("""
            SELECT * FROM properties
            WHERE delinquent_amount > 10000
              AND last_scraped_at > datetime('now', '-1 day')
            LIMIT 10
        """)

        suggestions = []
        for prop in high_value:
            # Get neighbors (same owner, same street, etc.)
            neighbors = lpm.get_neighbors(prop.id, limit=10)

            for neighbor in neighbors:
                if self.should_scrape(neighbor):
                    suggestions.append(TaskSuggestion(
                        url=neighbor.url,
                        priority=2,
                        queue='high',
                        metadata={'strategy': 'ripple', 'parent_id': prop.id}
                    ))

        return suggestions[:limit]
```

**Beat Schedule:** Every 10 minutes

---

### E. Sweeper Strategy (Linear / Blind)

**Purpose:** Pure discovery of unindexed records.

```python
class SweeperStrategy(Strategy):
    """Sequential discovery of new records."""

    def __init__(self, platform: str):
        self.platform = platform

    def suggest_tasks(self, limit: int) -> List[TaskSuggestion]:
        # Get last discovered ID
        last_id = lpm.get_metadata(f'sweeper_{self.platform}_last_id', 0)

        # Generate next batch of IDs to try
        urls = self.generate_urls(last_id, limit)

        # Update checkpoint
        lpm.set_metadata(f'sweeper_{self.platform}_last_id', last_id + limit)

        return [
            TaskSuggestion(
                url=url,
                priority=4,
                queue='low',
                metadata={'strategy': 'sweeper', 'discovery': True}
            )
            for url in urls
        ]
```

**Beat Schedule:** Every 30 minutes

---

## 5. Strategy Mixer

```python
class StrategyMixer:
    """Manages strategy execution with weighted allocation."""

    def __init__(self):
        self.strategies = {
            'chronos': (ChronosStrategy(), 0.10),    # 10%
            'targeted': (TargetedStrategy(), 0.50),  # 50%
            'hotspot': (HotspotStrategy(), 0.30),    # 30%
            'sweeper': (SweeperStrategy(), 0.10),    # 10%
        }
        self.min_guaranteed = 5  # Minimum tasks per strategy

    def execute(self, total_limit: int = 100):
        """Execute all strategies with weighted allocation."""
        results = {}

        for name, (strategy, weight) in self.strategies.items():
            # Calculate limit with minimum guarantee
            limit = max(
                self.min_guaranteed,
                int(total_limit * weight)
            )

            count = strategy.execute(limit)
            results[name] = count

        return results
```

---

## 6. Celery Beat Schedule

```python
app.conf.beat_schedule = {
    # Chronos: freshness maintenance
    'run-chronos': {
        'task': 'crawler.strategies.run_strategy',
        'schedule': crontab(minute='*/5'),
        'args': ['chronos', 50],
    },

    # Targeted: auction-focused
    'run-targeted': {
        'task': 'crawler.strategies.run_strategy',
        'schedule': crontab(minute=0),  # Every hour
        'args': ['targeted', 100],
    },

    # Hotspot: user interest
    'run-hotspot': {
        'task': 'crawler.strategies.run_strategy',
        'schedule': crontab(minute='*'),  # Every minute
        'args': ['hotspot', 20],
    },

    # Sweeper: discovery
    'run-sweeper': {
        'task': 'crawler.strategies.run_strategy',
        'schedule': crontab(minute='*/30'),
        'args': ['sweeper', 50],
    },

    # Full mixer run
    'run-mixer': {
        'task': 'crawler.strategies.run_mixer',
        'schedule': crontab(minute='*/15'),
        'args': [200],
    },
}
```

---

## 7. Signal Ingestion (Hotspot)

```python
@app.task
def ingest_user_signal(signal_type: str, data: dict):
    """Receive user interest signals from ecosystem."""

    if signal_type == 'view_region':
        lpm.execute("""
            INSERT INTO user_interests (county, state, created_at)
            VALUES (?, ?, datetime('now'))
        """, [data['county'], data['state']])

    elif signal_type == 'view_property':
        lpm.execute("""
            INSERT INTO user_interests (property_id, created_at)
            VALUES (?, datetime('now'))
        """, [data['property_id']])
```

**API Endpoint:**
```
POST /signals
{"type": "view_region", "county": "Miami-Dade", "state": "FL"}
```

---

## 8. User Stories

### US-1: Strategy Mixing & Starvation Protection
**As a** operator
**I want** Chronos to always get 10% of resources
**So that** the database doesn't develop blind spots

**Implementation:** `min_guaranteed = 5` in StrategyMixer

---

### US-2: User Interest Driven (Hotspot)
**As a** user
**I want** system to prioritize regions I'm viewing
**So that** I get fresh data for my research area

**Implementation:** HotspotStrategy + signal ingestion

---

### US-3: Discovery vs Update
**As a** researcher
**I want** to switch between discovery and enrichment
**So that** I can expand coverage or keep data fresh

**Implementation:** Sweeper (discovery) + Chronos (enrichment) with configurable weights

---

## 9. Implementation Tasks

| Task | Description | Complexity |
|------|-------------|------------|
| 1 | Implement Strategy base class | Low |
| 2 | Implement ChronosStrategy | Low |
| 3 | Implement TargetedStrategy | Medium |
| 4 | Implement HotspotStrategy | Medium |
| 5 | Implement RippleStrategy | Medium |
| 6 | Implement SweeperStrategy | Low |
| 7 | Implement StrategyMixer | Medium |
| 8 | Add Beat schedule configuration | Low |
| 9 | Add signal ingestion endpoint | Low |
| 10 | Add user_interests table to LPM | Low |

**Total: 10 tasks**

---

## 10. Constraints

- **C-1:** Strategy selection must complete in < 500ms
- **C-2:** Hotspot must respect rate limits (queue-based, not request-based)
- **C-3:** Must support runtime weight adjustment
- **C-4:** Must not starve any strategy completely

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
