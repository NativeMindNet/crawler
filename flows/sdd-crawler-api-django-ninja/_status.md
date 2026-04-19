# SDD Status: Crawler API Migration (Django Ninja)

**Flow:** `sdd-crawler-api-django-ninja`
**Current Phase:** SPECIFICATIONS
**Last Updated:** 2026-04-19

---

## Phase: REQUIREMENTS

- [x] Initial requirements draft from codebase/SDD analysis
- [x] Requirements approved by user

## Phase: SPECIFICATIONS

- [x] Detailed analysis of existing routes
- [x] Mapping FastAPI routes to Ninja routers
- [x] Definition of new API structure in `crawler/api/ninja/`
- [ ] Specifications approved by user

## Phase: PLAN

- [ ] Breakdown migration into atomic tasks
- [ ] Establish dependencies
- [ ] Plan approved by user

## Phase: IMPLEMENTATION

- [ ] Task 1: Initialize Django Ninja project structure
- [ ] Task 2: Implement Health & Metrics routers
- [ ] Task 3: Implement Config & Logs routers
- [ ] Task 4: Implement Task & Scrape routers
- [ ] Task 5: Implement Webhooks & Bulk routers
- [ ] Task 6: Final testing and switchover

---

## Blockers / Questions
- Django is not yet in `requirements.txt`.
- We need to decide whether to keep both APIs running simultaneously or switch entirely.
