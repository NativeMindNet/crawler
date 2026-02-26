# Specifications: Priority Scoring Engine

**Version:** 0.1
**Status:** DRAFT
**Last Updated:** 2026-02-02

---

## 1. Data Model

### 1.1 `parcel_priority` (Table or View)
We need to track the priority state for every parcel.

| Field | Type | Description |
| :--- | :--- | :--- |
| `parcel_id` | UUID/String | Foreign key to Parcel. |
| `priority_score` | Float | Calculated value (0.0 to 10.0). |
| `last_priority_update` | DateTime | When the score was last recalculated. |
| `next_scrape_at` | DateTime | The hard deadline for the next scrape. |
| `priority_tier` | Enum | [CRITICAL, HIGH, MEDIUM, LOW, HIBERNATION] |

---

## 2. Priority Scoring Algorithm

The score is calculated as: 
`FinalScore = BaseScore * Multipliers + TimeUrgency`

### 2.1 Base Scores (by Status)
| Status | Base Score | Tier |
| :--- | :--- | :--- |
| **Paid (No Liens)** | 0.1 | HIBERNATION |
| **Paid (Active Liens)** | 1.0 | LOW |
| **Delinquent (Pre-Lien)** | 5.0 | HIGH |
| **OTC Available** | 6.0 | HIGH |
| **Multiple Lien Holders** | 7.5 | HIGH |
| **Foreclosure/TDA Filed** | 9.0 | CRITICAL |
| **Auction Scheduled** | 10.0 | CRITICAL |

### 2.2 Multipliers
- **Arizona Feb 2026 Boost:** `x2.0` if `state == 'AZ'` and `date < 2026-02-28`.
- **Miw's Sweet Spot:** `x1.5` if `market_value / tax_due > 20`.
- **User Interest:** `x5.0` if the property was viewed in the last 24 hours (Hotspot).

### 2.3 Time Urgency (Gravity)
- Score increases by `0.1` for every day since `last_scraped_at`.
- For **Paid** properties, gravity is capped at `1.0`.
- For **Delinquent** properties, gravity is uncapped.

---

## 3. Scrape Frequency (TTL)

Based on the calculated Tier, we determine the `next_scrape_at`:

| Tier | TTL (Cooldown) | Max Latency |
| :--- | :--- | :--- |
| **CRITICAL** | 12 hours | 24 hours |
| **HIGH** | 3 days | 7 days |
| **MEDIUM** | 7 days | 14 days |
| **LOW** | 30 days | 60 days |
| **HIBERNATION**| 90 days | 180 days |

---

## 4. Special Triggers (Global Events)

Certain events force a priority recalculation for large batches:

1.  **Tax Due Date + 1 Day:** All "Paid" properties in that county/state jump to **HIGH** for one check to verify payment.
2.  **Auction List Release:** When a new auction file is parsed, all referenced parcels jump to **CRITICAL**.

---

## 5. Implementation Strategy

1.  **SQL View:** Create a `v_parcel_scrape_priority` that joins `parcels` with `liens` and `auctions` to calculate these scores in real-time.
2.  **Scheduler Integration:** The `suggest_tasks` method in the `TraversalModule` will simply do:
    `SELECT parcel_id FROM v_parcel_scrape_priority WHERE next_scrape_at <= NOW() ORDER BY priority_score DESC LIMIT ?`
