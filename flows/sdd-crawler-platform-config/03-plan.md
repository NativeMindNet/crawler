# Implementation Plan: sdd-taxlien-parser-platforms-configs

> **Version:** 2.0 (Standard SDD Structure)
> **Status:** APPROVED
> **Last Updated:** 2026-02-22
> **Specifications:** [02-specifications.md](02-specifications.md)

---

## Summary

Complete specs-as-source coverage for all 27 platforms with all 7 config types (selectors, mapping, manifest, counties, business_rules, schedule, discovery). Total: 189 config files generated from single specification.

---

## Task Breakdown

### Phase 1: Infrastructure

#### Task 1.1: Create ConfigLoader Utility
- **Description:** Create `platforms/config_loader.py` to load and merge configs
- **Files:**
  - `platforms/config_loader.py` - Create
- **Dependencies:** None
- **Verification:** Unit tests for load_config() with default + overrides merging
- **Complexity:** Medium

```python
# config_loader.py skeleton
def load_config(platform: str, file_type: str, county_key: str = None) -> dict:
    """Load config file and merge default with county-specific overrides."""
    base_path = f"platforms/{platform}/{file_type}.json"
    with open(base_path) as f:
        config = json.load(f)
    
    if county_key and "overrides" in config and county_key in config["overrides"]:
        merged = {**config["default"], **config["overrides"][county_key]}
        return merged
    return config.get("default", config)
```

---

### Phase 2: Tier 1 Migration (Priority)

#### Task 2.1: QPublic Config Migration
- **Description:** Migrate qpublic to new config structure
- **Files:**
  - `platforms/qpublic/counties.json` - Rename from auto_config.json
  - `platforms/qpublic/selectors.json` - Extract from configs_qpublic.js
  - `platforms/qpublic/manifest.json` - Create
  - `platforms/qpublic/business_rules.json` - Create
  - `platforms/qpublic/schedule.json` - Create
  - `platforms/qpublic/discovery.json` - Create
- **Dependencies:** Task 1.1
- **Verification:** ConfigLoader loads qpublic configs correctly
- **Complexity:** Medium

#### Task 2.2: Beacon Config Migration
- **Description:** Migrate beacon to new config structure
- **Files:**
  - `platforms/beacon/counties.json` - Rename/extract from tier1_config.py
  - `platforms/beacon/selectors.json` - Extract from legacy JS
  - `platforms/beacon/manifest.json` - Create
  - `platforms/beacon/business_rules.json` - Create
  - `platforms/beacon/schedule.json` - Create
  - `platforms/beacon/discovery.json` - Create
- **Dependencies:** Task 1.1
- **Verification:** ConfigLoader loads beacon configs correctly
- **Complexity:** Medium

---

### Phase 3: Global Migration

#### Task 3.1: Migrate auto_config.json Files
- **Description:** Iterate through all platforms/*/auto_config.json and rename to counties.json
- **Files:** All `platforms/*/auto_config.json` → `platforms/*/counties.json`
- **Dependencies:** None
- **Verification:** All auto_config.json files renamed
- **Complexity:** Low

#### Task 3.2: Create manifest.json for All Platforms
- **Description:** Create basic manifest.json with technical specs for each platform
- **Files:** `platforms/*/manifest.json` (27 files)
- **Dependencies:** None
- **Verification:** All 27 platforms have manifest.json
- **Complexity:** Low

#### Task 3.3: Redistribute tier1_config.py Counties
- **Description:** Extract county data from tier1_config.py into platform-specific counties.json
- **Files:**
  - `platforms/*/counties.json` - Modify (add county data)
  - `scrapers/tier1_config.py` - Delete (after migration)
- **Dependencies:** Task 3.1
- **Verification:** All counties mapped in platform configs
- **Complexity:** Medium

---

### Phase 4: Tier 2 Config Completion

#### Task 4.1: Extract Selectors from Parsers
- **Description:** For platforms with parsers (bid4assets, fidlar, governmax), extract selectors
- **Files:**
  - `platforms/bid4assets/selectors.json` - Create
  - `platforms/bid4assets/mapping.json` - Create
  - `platforms/fidlar/selectors.json` - Create
  - `platforms/fidlar/mapping.json` - Create
  - `platforms/governmax/selectors.json` - Create
  - `platforms/governmax/mapping.json` - Create
- **Dependencies:** None
- **Verification:** Selectors match parser patterns
- **Complexity:** Medium

#### Task 4.2: Create Generic Selectors for Remaining Platforms
- **Description:** For platforms without parsers (cama, civic_source, egov, etc.), create generic selectors
- **Files:** selectors.json + mapping.json for 8 platforms
- **Dependencies:** None
- **Verification:** All platforms have selectors.json and mapping.json
- **Complexity:** Low

---

### Phase 5: Tier 3 Platform Creation

#### Task 5.1: Create Tier 3 Platform Directories
- **Description:** Create platform directories and all 7 config files for CRITICAL/HIGH priority platforms
- **Files:** 7 platforms × 7 files = 49 files
  - `platforms/kofile/` (7 files)
  - `platforms/cott_systems/` (7 files)
  - `platforms/mytaxbill/` (7 files)
  - `platforms/vgsi/` (7 files)
  - `platforms/avitar/` (7 files)
  - `platforms/nh_tax_kiosk/` (7 files)
  - `platforms/searchiqs/` (7 files)
- **Dependencies:** None
- **Verification:** All 49 files created with valid JSON
- **Complexity:** Low

---

### Phase 6: Code Integration

#### Task 6.1: Update platform_detector.py
- **Description:** Update to use counties.json instead of tier1_config.py
- **Files:**
  - `tools/platform_detector.py` - Modify
- **Dependencies:** Task 3.3
- **Verification:** platform_detector.py runs without errors
- **Complexity:** Low

#### Task 6.2: Update Scrapers to Use ConfigLoader
- **Description:** Update scrapers to load configs via ConfigLoader
- **Files:** `scrapers/*.py` - Modify
- **Dependencies:** Task 1.1
- **Verification:** Scrapers run with new config system
- **Complexity:** Medium

#### Task 6.3: Delete Legacy Config Files
- **Description:** Remove tier1_config.py and legacy JS config files
- **Files:**
  - `scrapers/tier1_config.py` - Delete
  - `configs/legacy_js/*.js` - Move to archive
- **Dependencies:** Task 6.2
- **Verification:** No code references deleted files
- **Complexity:** Low

---

### Phase 7: Verification

#### Task 7.1: Validate Configs Against HTML Samples
- **Description:** Test selectors on 920 HTML samples from taxlien-storage
- **Files:** Validation script
- **Dependencies:** All config files created
- **Verification:** Selectors extract data correctly from samples
- **Complexity:** High

#### Task 7.2: Run Integration Tests
- **Description:** Test ConfigLoader with sample overrides
- **Files:** Test script
- **Dependencies:** Task 1.1, all configs created
- **Verification:** All tests pass
- **Complexity:** Medium

---

## Dependency Graph

```
Task 1.1 (ConfigLoader)
    │
    ├─→ Task 2.1 (QPublic) ─┐
    ├─→ Task 2.2 (Beacon) ──┤
    │                       │
    ├─→ Task 3.1 (auto_config rename)
    │                       │
    ├─→ Task 3.2 (manifest.json)
    │                       │
    ├─→ Task 3.3 (tier1 migration) ─→ Task 6.1 (platform_detector)
    │                                  │
    ├─→ Task 4.1 (Tier 2 selectors) ──┤
    │                                  │
    ├─→ Task 4.2 (Tier 2 generic) ────┤
    │                                  │
    ├─→ Task 5.1 (Tier 3 platforms) ──┤
                                       │
    └──────────────────────────────────┘
                                       ↓
                              Task 6.2 (Scrapers update)
                                       │
                                       ↓
                              Task 6.3 (Legacy cleanup)
                                       │
                                       ↓
                              Task 7.1 (HTML validation)
                              Task 7.2 (Integration tests)
```

---

## File Change Summary

| File | Action | Reason |
|------|--------|--------|
| `platforms/config_loader.py` | Create | New utility for loading configs |
| `platforms/*/selectors.json` (27) | Create | Data extraction selectors |
| `platforms/*/mapping.json` (27) | Create | Field mapping to schema |
| `platforms/*/manifest.json` (27) | Create | Technical specifications |
| `platforms/*/counties.json` (27) | Create/Rename | County registry |
| `platforms/*/business_rules.json` (27) | Create | Normalization rules |
| `platforms/*/schedule.json` (27) | Create | Scraping schedule |
| `platforms/*/discovery.json` (27) | Create | URL patterns |
| `scrapers/tier1_config.py` | Delete | Migrated to counties.json |
| `tools/platform_detector.py` | Modify | Use new config system |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Selectors don't work on real HTML | Medium | High | Validate against 920 HTML samples before marking complete |
| County data lost in migration | Low | High | Backup tier1_config.py before deletion, verify all counties mapped |
| ConfigLoader performance issues | Low | Medium | Profile loading time, cache configs if needed |
| Parser breaks with new configs | Medium | Medium | Test each parser after config migration |

---

## Rollback Strategy

If implementation fails or needs to be reverted:

1. Restore `scrapers/tier1_config.py` from backup
2. Restore `platforms/*/auto_config.json` from `platforms/*/counties.json`
3. Revert `tools/platform_detector.py` to use tier1_config.py
4. Delete `platforms/config_loader.py`

---

## Checkpoints

After each phase, verify:

- [ ] All JSON files are valid (parse without errors)
- [ ] ConfigLoader loads and merges configs correctly
- [ ] Platform detector still works
- [ ] No references to deleted legacy files

---

## Open Implementation Questions

- [ ] Should we validate all selectors before marking Phase 5 complete?
- [ ] Should Tier 3 platforms have full configs or minimal placeholders initially?

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]
