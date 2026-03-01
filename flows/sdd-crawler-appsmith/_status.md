# Status: sdd-crawler-appsmith

> **SDD Flow Status Page**
> Scope: AppSmith integration for Universal Crawler (self-contained)

**Current Phase:** REQUIREMENTS
**Phase Status:** DRAFTING
**Last Updated:** 2026-03-01 by Claude
**Version:** 1.0

---

## Scope Definition

**This SDD owns:** AppSmith UI components that interact ONLY with crawler's own API.

**This SDD does NOT own:**
- K8s service discovery (that's taxlien-parser's job)
- Cross-crawler orchestration
- Platform registry

**Key principle:** Crawler is platform-agnostic. AppSmith here manages ONE crawler instance.

---

## Blockers

- None

---

## Progress

- [ ] Requirements drafted
- [ ] Requirements approved
- [ ] Specifications drafted
- [ ] Specifications approved
- [ ] Plan drafted
- [ ] Plan approved
- [ ] Implementation started
- [ ] Implementation complete

---

## Context Notes

- Crawler doesn't know about other crawlers
- Crawler doesn't know what platform it serves
- AppSmith for crawler = management of tasks, health, config for THIS instance only
- External orchestrator (taxlien-parser) handles multi-crawler coordination

---

## Related SDDs

- `sdd-crawler-architecrure` — Overall crawler architecture
- `taxlien-parser/flows/sdd-taxlien-parser-appsmith-v2` — Parser-side AppSmith (multi-crawler orchestration)

---

## Next Actions

1. Draft requirements for single-instance crawler management UI
2. Define API endpoints needed
3. Review with user
