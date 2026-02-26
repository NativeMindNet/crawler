# Requirements: Delinquency-Based Priority Parsing

**Version:** 0.1
**Status:** DRAFT
**Last Updated:** 2026-02-02

---

## 1. Goal
Implement a dynamic prioritization strategy for the parcel parser that focuses resources on properties with tax delinquency (high probability of auction/lien) while deprioritizing compliant properties.

## 2. Context & Motivation
- **Business Goal:** Maximize the "Freshness" of data for actionable properties (those likely to go to auction) within the constraints of server resources and site rate limits.
- **Reference:** `sdd-miw-gift` emphasizes focusing on "Sweet Spots" (chronic delinquent, low redemption prob) and specifically targeting the Arizona Feb 2026 auction.
- **Current Problem:** The parser might be spending equal effort updating safe, paid-up properties as it does on distressed properties.
- **User Hypothesis:** 
    - **Delinquent (Late Payment):** High Priority. Implies potential lien/deed auction. Needs frequent monitoring (e.g., daily/weekly) to catch status changes, new fees, or auction scheduling.
    - **Compliant (Paid on Time):** Low Priority. If a property has no liens/deeds and taxes are paid, it's "safe" until the next tax due date. Updating it once a month or even less is sufficient.

## 3. User Stories

### US-1: Delinquency-Based Frequency
**As a** system
**I want** to update properties with `delinquent_amount > 0` or `tax_status != 'PAID'` more frequently
**So that** I capture the evolution of debt and don't miss auction triggers.

### US-2: Compliant Property Hibernation
**As a** system
**I want** to set a long "cooldown" period for properties with `tax_status == 'PAID'` and no active liens
**So that** I don't waste bandwidth on static records.

### US-3: Tax Cycle Awareness
**As a** system
**I want** to automatically increase priority for *all* properties when a major tax due date approaches (e.g., Nov 1st / Mar 1st in many states)
**So that** I can detect who missed the new payment deadline.

### US-4: State-Type & Status Awareness (Lien/Deed/Hybrid)
**As a** strategist
**I want** the system to apply different priority curves based on the state's legal model and the property's current phase (OTC vs Auction vs Foreclosure)
**So that** I focus resources on the most critical moments for each investment type.

## 4. Functional Requirements

### FR-1: Priority Calculation Logic
- The system must calculate a `next_scrape_date` or `priority_score` based on:
    1.  **Delinquency Status:** Is there an outstanding balance?
    2.  **Lien/Deed Existence:** Are there active liens or deed sale flags?
    3.  **Time to Auction:** If an auction date is known, priority increases exponentially as it approaches.
    4.  **Tax Calendar:** Is a payment deadline approaching?

### FR-2: State-Specific Priority Matrix

| State Type | Status | Priority | Frequency | Reasoning |
| :--- | :--- | :--- | :--- | :--- |
| **AZ (Judicial)** | **Delinquent** (Pre-Lien) | HIGH | Weekly | Catching properties before Tax Lien Auction. |
| **AZ (Judicial)** | **Active Lien** (Waiting) | LOW | Monthly | 3-year quiet period. Monitor for redemption only. |
| **AZ (Judicial)** | **Foreclosure Action** | **CRITICAL** | **Daily** | Court case filed. Holder likely to get Deed directly (No public auction). Track strictly if WE are the holder. |
| **FL (Auction)** | **Delinquent** | HIGH | Weekly | Pre-lien monitoring. |
| **FL (Auction)** | **Active Lien** | LOW | Monthly | 2-year wait. |
| **FL (Auction)** | **TDA Filed** (Application) | **SUPER HOT** | **Daily** | **Public Deed Auction** triggered! Opportunity for ALL investors, not just holder. |
| **Deed (UT, SD)** | **Auction Scheduled** | **CRITICAL** | **Daily** | Property sale imminent. |

### FR-3: Multi-Holder "Stacking" Boost
- **Condition:** If a property has active liens from **multiple different investors** (e.g., Year 2023 held by Investor A, Year 2024 held by Investor B).
- **Action:** Increase Priority to **HIGH** regardless of state type.
- **Reasoning:** High competition between investors implies high value or imminent foreclosure action.

### FR-4: Integration with `sdd-taxlien-parser-strategy`
- This logic should likely be implemented as a specific **Strategy** (e.g., "RiskBasedStrategy") within the Traversal Strategy Module.

### FR-4: Arizona Feb 2026 Focus (Immediate)
- **Constraint:** Ensure this priority logic specifically aggressively targets Arizona counties (Maricopa, Pinal, Pima, etc.) for the upcoming Feb 2026 auctions as per `sdd-miw-gift`.
- **Special Rule:** For AZ Feb 2026, treat ALL Delinquent properties as "Auction Scheduled" priority until the auction ends.

## 5. Questions & Clarifications
1.  **Delinquency Definition:** Does "delinquent" just mean `current_year_tax_due > 0` after due date, or does it require `prior_years_owed > 0`? (Assumption: Any past due amount triggers higher priority).
2.  **Frequency:**
    - High Priority (Delinquent): Daily? Weekly?
    - Low Priority (Paid): Monthly? Quarterly?
3.  **Triggers:** What specific field in the standardized `Parcel` model indicates "delinquency" reliably across parsers? (Likely `tax_status`, `total_due`, or specific flags).

---

## 6. Acceptance Criteria
- [ ] Logic defines at least 2 distinct priority tiers (High/Low).
- [ ] "Paid" properties are not re-scraped within X days (e.g., 30 days) unless a global trigger occurs.
- [ ] "Delinquent" properties are re-scraped within Y days (e.g., 3-7 days).
