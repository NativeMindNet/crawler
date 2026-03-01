# Requirements: Priority-Based Task Scheduling (Celery Queues)

**Version:** 1.0
**Status:** DRAFT
**Last Updated:** 2026-03-01

---

## 1. Goal

Implement dynamic task prioritization using **Celery priority queues** to focus resources on high-value properties (delinquent, auction-imminent) while deprioritizing compliant properties.

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      PRIORITY QUEUE SYSTEM                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    Priority Calculator                           │   │
│  │  Property State → Priority Score → Queue Assignment              │   │
│  └──────────────────────────────┬──────────────────────────────────┘   │
│                                 │                                       │
│                                 ▼                                       │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                       Redis Broker                               │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │   │
│  │  │  urgent  │ │   high   │ │ default  │ │   low    │           │   │
│  │  │ (daily)  │ │ (weekly) │ │(bi-week) │ │(monthly) │           │   │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │   │
│  │       │            │            │            │                   │   │
│  │       └────────────┴─────┬──────┴────────────┘                   │   │
│  └──────────────────────────┼──────────────────────────────────────┘   │
│                             │                                           │
│                             ▼                                           │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     Celery Workers                               │   │
│  │         Consume: urgent → high → default → low                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Priority Queues

### Queue Definitions

| Queue | Priority | Frequency | Use Case |
|-------|----------|-----------|----------|
| `urgent` | 1 (highest) | Daily | Foreclosure, TDA Filed, Auction Scheduled |
| `high` | 2 | Weekly | Delinquent, Pre-Lien |
| `default` | 3 | Bi-weekly | Normal properties |
| `low` | 4 (lowest) | Monthly | Paid/Compliant, Hibernated |

### Worker Configuration

```bash
# Workers consume queues in priority order
celery -A crawler worker -Q urgent,high,default,low -c 4

# Dedicated urgent worker (optional)
celery -A crawler worker -Q urgent -c 2 --hostname=urgent@%h
```

---

## 4. Priority Matrix by State Type

### Arizona (Judicial Foreclosure)

| Status | Queue | Frequency | Reasoning |
|--------|-------|-----------|-----------|
| **Foreclosure Action** | `urgent` | Daily | Court case filed, deed imminent |
| **Delinquent** (Pre-Lien) | `high` | Weekly | Catching before auction |
| **Active Lien** (Waiting) | `low` | Monthly | 3-year quiet period |
| **Paid** | `low` | Monthly | No action needed |

### Florida (Auction State)

| Status | Queue | Frequency | Reasoning |
|--------|-------|-----------|-----------|
| **TDA Filed** | `urgent` | Daily | Public deed auction triggered |
| **Delinquent** | `high` | Weekly | Pre-lien monitoring |
| **Active Lien** | `low` | Monthly | 2-year wait |
| **Paid** | `low` | Monthly | No action needed |

### Deed States (UT, SD, etc.)

| Status | Queue | Frequency | Reasoning |
|--------|-------|-----------|-----------|
| **Auction Scheduled** | `urgent` | Daily | Property sale imminent |
| **Delinquent** | `high` | Weekly | Pre-auction |
| **Paid** | `low` | Monthly | No action needed |

---

## 5. Priority Calculator

```python
from enum import IntEnum
from datetime import datetime, timedelta

class Priority(IntEnum):
    URGENT = 1
    HIGH = 2
    DEFAULT = 3
    LOW = 4

class PriorityCalculator:
    """Calculate task priority based on property state."""

    def calculate(self, property_data: dict) -> tuple[Priority, str]:
        """
        Returns (priority, queue_name)
        """
        status = property_data.get('tax_status', '')
        delinquent_amount = property_data.get('delinquent_amount', 0)
        auction_date = property_data.get('auction_date')
        state_type = property_data.get('state_type', 'lien')
        has_active_liens = property_data.get('has_active_liens', False)
        tda_filed = property_data.get('tda_filed', False)
        foreclosure_action = property_data.get('foreclosure_action', False)

        # URGENT: Imminent events
        if foreclosure_action:
            return Priority.URGENT, 'urgent'

        if tda_filed:
            return Priority.URGENT, 'urgent'

        if auction_date:
            days_to_auction = (auction_date - datetime.now()).days
            if days_to_auction <= 30:
                return Priority.URGENT, 'urgent'
            if days_to_auction <= 90:
                return Priority.HIGH, 'high'

        # HIGH: Active delinquency
        if delinquent_amount > 0:
            return Priority.HIGH, 'high'

        if status in ('DELINQUENT', 'PAST_DUE', 'UNPAID'):
            return Priority.HIGH, 'high'

        # LOW: Stable/Compliant
        if status in ('PAID', 'CURRENT', 'COMPLIANT'):
            return Priority.LOW, 'low'

        if has_active_liens and not delinquent_amount:
            # Waiting period (e.g., FL 2-year, AZ 3-year)
            return Priority.LOW, 'low'

        # DEFAULT: Everything else
        return Priority.DEFAULT, 'default'

    def apply_boosts(self, priority: Priority, property_data: dict) -> Priority:
        """Apply priority boosts for special conditions."""

        # Multi-holder stacking: multiple investors = high competition
        if property_data.get('lien_holder_count', 0) > 1:
            return min(priority, Priority.HIGH)

        # Tax cycle awareness: boost all near payment deadline
        if self.is_near_tax_deadline(property_data.get('state')):
            return min(priority, Priority.HIGH)

        return priority

    def is_near_tax_deadline(self, state: str) -> bool:
        """Check if we're near a major tax deadline."""
        now = datetime.now()

        # Common deadlines
        deadlines = {
            'FL': [(11, 1), (3, 31)],  # Nov 1, Mar 31
            'AZ': [(10, 1), (3, 1)],   # Oct 1, Mar 1
        }

        if state in deadlines:
            for month, day in deadlines[state]:
                deadline = datetime(now.year, month, day)
                days_until = (deadline - now).days
                if 0 <= days_until <= 14:  # Within 2 weeks
                    return True

        return False
```

---

## 6. Task Submission with Priority

```python
@app.task(bind=True)
def schedule_scrape(self, url: str, property_data: dict):
    """Schedule scrape task with calculated priority."""

    calculator = PriorityCalculator()
    priority, queue = calculator.calculate(property_data)
    priority = calculator.apply_boosts(priority, property_data)

    # Submit to appropriate queue
    scrape_task.apply_async(
        args=[url],
        kwargs={'property_data': property_data},
        queue=queue,
        priority=priority.value  # Celery priority within queue
    )

    return {'url': url, 'queue': queue, 'priority': priority.name}
```

---

## 7. Strategy Integration

```python
class PriorityStrategy:
    """Strategy that generates tasks with priority awareness."""

    def __init__(self, calculator: PriorityCalculator):
        self.calculator = calculator

    def suggest_tasks(self, limit: int = 100) -> list[dict]:
        """Suggest tasks ordered by priority."""

        # Get candidates from LPM
        candidates = lpm.get_stale_properties(limit=limit * 2)

        # Calculate priorities
        prioritized = []
        for prop in candidates:
            priority, queue = self.calculator.calculate(prop)
            prioritized.append({
                'property': prop,
                'priority': priority,
                'queue': queue
            })

        # Sort by priority (urgent first)
        prioritized.sort(key=lambda x: x['priority'])

        return prioritized[:limit]

    def execute(self, limit: int = 100):
        """Generate and submit priority-sorted tasks."""
        tasks = self.suggest_tasks(limit)

        for task in tasks:
            scrape_task.apply_async(
                args=[task['property']['url']],
                queue=task['queue']
            )
```

---

## 8. Celery Configuration

```python
# celery_config.py

app.conf.task_queues = [
    Queue('urgent', routing_key='urgent'),
    Queue('high', routing_key='high'),
    Queue('default', routing_key='default'),
    Queue('low', routing_key='low'),
]

app.conf.task_default_queue = 'default'

# Rate limiting per queue (optional)
app.conf.task_annotations = {
    'crawler.tasks.scrape_task': {
        'rate_limit': '10/m',  # Global rate limit
    },
}

# Worker prefetch (process urgent first)
app.conf.worker_prefetch_multiplier = 1
```

---

## 9. Monitoring Priority Distribution

```python
@app.task
def report_queue_stats():
    """Report queue depth for monitoring."""
    from celery import current_app

    inspect = current_app.control.inspect()

    stats = {
        'urgent': len(inspect.reserved().get('urgent', [])),
        'high': len(inspect.reserved().get('high', [])),
        'default': len(inspect.reserved().get('default', [])),
        'low': len(inspect.reserved().get('low', [])),
    }

    # Log or send to metrics
    logger.info(f"Queue stats: {stats}")
    return stats
```

**Flower Dashboard:** Shows queue depth per queue in real-time.

---

## 10. User Stories

### US-1: Delinquency-Based Frequency
**As a** system
**I want** to update delinquent properties more frequently
**So that** I capture debt evolution and auction triggers

**Implementation:** Delinquent → `high` queue (weekly)

---

### US-2: Compliant Property Hibernation
**As a** system
**I want** to set long cooldown for paid properties
**So that** I don't waste bandwidth on static records

**Implementation:** Paid → `low` queue (monthly)

---

### US-3: Tax Cycle Awareness
**As a** system
**I want** to boost priority near tax deadlines
**So that** I detect who missed payment

**Implementation:** `apply_boosts()` checks deadline proximity

---

### US-4: Auction Countdown
**As a** system
**I want** exponentially increasing priority as auction approaches
**So that** I have freshest data at critical moment

**Implementation:** Days to auction → queue mapping (30d = urgent, 90d = high)

---

## 11. Implementation Tasks

| Task | Description | Complexity |
|------|-------------|------------|
| 1 | Define Celery queues (urgent/high/default/low) | Low |
| 2 | Implement PriorityCalculator class | Medium |
| 3 | Implement priority boosts (multi-holder, tax cycle) | Medium |
| 4 | Integrate with Strategy module | Low |
| 5 | Add queue stats reporting | Low |
| 6 | Configure worker queue consumption order | Low |
| 7 | Add Flower queue monitoring | Low |

**Total: 7 tasks**

---

## 12. Constraints

- **C-1:** Must support 4 priority levels minimum
- **C-2:** Must not starve low-priority queue completely
- **C-3:** Must recalculate priority on each scrape (status may change)
- **C-4:** Must handle unknown properties as `default`

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
