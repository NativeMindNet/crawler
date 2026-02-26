# Specifications: sdd-taxlien-parser-platforms-configs

> **Version:** 6.0 (Standard SDD Structure + Separate Platform Configs)
> **Status:** APPROVED
> **Last Updated:** 2026-02-22
> **Requirements:** [01-requirements.md](01-requirements.md)
> **Platform Configs:** [platforms_configs.md](platforms_configs.md)

---

## Overview

This document provides architectural specifications for the taxlien-parser platform configuration system. Following the **specs-as-source** approach, all configurations are defined here and in `platforms_configs.md`, then generated into `platforms/{name}/` JSON files.

**Related Documents:**
- `platforms_configs.md` — Complete specifications for all 7 config types for all 27 platforms

---

## Affected Systems

| System | Impact | Notes |
|--------|--------|-------|
| `platforms/*/` | Modify | All 27 platforms get 7 JSON config files each |
| `parsers/platforms/` | No change | Parsers use configs via ConfigLoader |
| `platforms/config_loader.py` | Create | New utility to load and merge configs |
| `tools/platform_detector.py` | Modify | Use counties.json instead of tier1_config.py |

---

## Architecture

### Config Inheritance Model

All JSON configuration files (except `manifest.json` and `counties.json`) follow this structure:

```json
{
  "default": {
    "key": "value"
  },
  "overrides": {
    "county_key": {
      "key": "overridden_value"
    }
  }
}
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│  02-specifications.md + platforms_configs.md            │
│  (Source of Truth)                                      │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Generated
                          ▼
┌─────────────────────────────────────────────────────────┐
│  platforms/{name}/                                      │
│  ├── selectors.json        (default + overrides)        │
│  ├── mapping.json          (default + overrides)        │
│  ├── manifest.json         (technical specs)            │
│  ├── counties.json         (county registry)            │
│  ├── business_rules.json   (default + overrides)        │
│  ├── schedule.json         (default + overrides)        │
│  └── discovery.json        (default + overrides)        │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Used by
                          ▼
┌─────────────────────────────────────────────────────────┐
│  platforms/config_loader.py                             │
│  - load_config(platform, file_type, county_key)         │
│  - Merges default + overrides                           │
└─────────────────────────────────────────────────────────┘
                          │
                          │ Provides to
                          ▼
┌─────────────────────────────────────────────────────────┐
│  scrapers/{platform}_scraper.py                         │
│  parsers/{platform}_parser.py                           │
└─────────────────────────────────────────────────────────┘
```

---

## Data Models

### 7 Config File Types

| # | File | Description | Has Overrides |
|---|------|-------------|---------------|
| 1 | selectors.json | CSS/XPath selectors for scraping | ✅ |
| 2 | mapping.json | Field mapping to ParcelData schema | ✅ |
| 3 | manifest.json | Technical specs (engine type, rate limits) | ❌ |
| 4 | counties.json | County-to-platform mapping | ❌ |
| 5 | business_rules.json | Data normalization rules | ✅ |
| 6 | schedule.json | Scraping frequency | ✅ |
| 7 | discovery.json | URL patterns and ID validation | ✅ |

### manifest.json Structure

```json
{
  "platform_id": "string",
  "platform_name": "string (optional)",
  "data_type": "assessor|tax|recorder|gis|auction",
  "coverage": "string (optional)",
  "engine_type": "stateless|stateful|api",
  "scraping": {
    "rate_limit": "N/m",
    "delay_ms": number,
    "use_proxy": boolean,
    "cloudflare": boolean,
    "impersonate": "chrome110 (optional)"
  },
  "capabilities": {
    "has_parcels": boolean,
    "has_taxes": boolean,
    "has_records": boolean,
    "has_gis": boolean,
    "has_auctions": boolean,
    "has_deeds": boolean,
    "has_delinquency": boolean
  }
}
```

### counties.json Structure

```json
{
  "counties": {
    "{state}_{county}": {
      "state": "XX",
      "county": "County Name",
      "tier": 1|2|3,
      "score": "X/4",
      "priority": number,
      "platforms": {
        "assessor": "platform_id",
        "tax": "platform_id",
        "gis": "platform_id",
        "recorder": "platform_id|null"
      },
      "urls": {
        "assessor": "https://...",
        "tax": "https://...",
        "gis": "https://...",
        "recorder": "https://..."
      },
      "params": {
        "AppID": "XXX"
      }
    }
  }
}
```

---

## Platform Summary

### Platform Index (27 platforms)

| # | Platform | Tier | Data Type | Priority |
|---|----------|------|-----------|----------|
| 1-9 | custom_gis, qpublic, beacon, tyler, arcgis, netronline, floridatax, myfloridacounty, county-taxes | Tier 1 | Parcels/Taxes | MUST HAVE |
| 10-20 | bid4assets, fidlar, governmax, cama, civic_source, egov, greenwoodmap, kcsgis, propertymax, alabamagis, tyler_technologies | Tier 2 | Various | HIGH/MEDIUM |
| 21-27 | kofile, cott_systems, mytaxbill, vgsi, avitar, nh_tax_kiosk, searchiqs | Tier 3 | Documents/Taxes | CRITICAL/HIGH |

**Complete configs:** See `platforms_configs.md`

---

## Edge Cases and Considerations

### Platform Variations
- Some platforms have multiple URL patterns (e.g., qpublic.net vs qpublic.schneidercorp.com)
- **Solution:** Use `overrides` in selectors.json for county-specific variations

### Missing Parsers
- 8 platforms in `/platforms/` don't have corresponding parsers
- **Solution:** Create generic selectors, document in metadata that parsers are needed

### Tier 3 Integration
- New platforms need scrapers and parsers eventually
- **For now:** Create config-only placeholders
- **Future:** Implement scrapers/parsers in separate SDD flows

### Validation
- Selectors should be validated against real HTML
- Currently: 920 HTML samples in taxlien-storage
- **Validation approach:** Test selectors on samples, refine as needed

---

## Dependencies

### Requires
- Python 3.x with BeautifulSoup4, lxml
- Access to taxlien-storage HTML samples for validation

### Blocks
- Parser implementation depends on config completion
- ConfigLoader utility must be created before parsers can use new configs

---

## Integration Points

### External Systems
- taxlien-storage: HTML samples for validation

### Internal Systems
- platforms/config_loader.py: Loads and merges configs
- scrapers/: Use configs for extraction
- parsers/: Use configs for field mapping
- tools/platform_detector.py: Uses counties.json

---

## Testing Strategy

### Unit Tests
- [ ] ConfigLoader loads configs correctly
- [ ] Override merging works as expected
- [ ] All 27 platforms have valid JSON configs

### Integration Tests
- [ ] Parsers can load and use configs
- [ ] Selectors work on real HTML samples

### Manual Verification
- [ ] Verify selectors on 920 HTML samples
- [ ] Confirm all counties are properly mapped

---

## Migration / Rollout

### Phase 1: Infrastructure
1. Create `platforms/config_loader.py`
2. Implement `load_config(platform, file_type, county_key=None)`
3. Support merging `default` and `overrides` dictionaries

### Phase 2: Config Migration
1. Rename `platforms/*/auto_config.json` to `platforms/*/counties.json`
2. Extract selectors from legacy JS files to `selectors.json`
3. Create all 7 config files for each platform

### Phase 3: Code Integration
1. Update `tools/platform_detector.py` to use `counties.json`
2. Update scrapers to use ConfigLoader
3. Delete `scrapers/tier1_config.py`

### Phase 4: Verification
1. Run platform_detector.py to ensure it still works
2. Test ConfigLoader with sample overrides
3. Validate selectors against HTML samples

---

## Open Design Questions

- [ ] Should we validate all selectors against HTML samples before marking complete?
- [ ] Should Tier 3 platforms have full configs or minimal placeholders?

---

## Approval

- [ ] Reviewed by: [name]
- [ ] Approved on: [date]
- [ ] Notes: [any conditions or clarifications]

---

## Appendices

### Appendix A: Selector Pattern Types

- **CSS Selectors:** `#id`, `.class`, `[attr]`, `#id.class[attr]`
- **XPath-like:** `td:contains('Parcel') + td`, `th:contains('Label') + td`
- **Regex:** `string:regex(/pattern/i)`
- **JavaScript Patterns:** `PIN=([0-9\\-A-Z]+)`, `mapURL\s*=\s*['"]([^'"]+)['"]`

### Appendix B: County Overrides

| Platform | County Key | Override Fields |
|----------|------------|-----------------|
| custom_gis | fl_union | parcel_id_patterns, owner_patterns |
| custom_gis | fl_columbia | parcel_id_patterns, owner_patterns |
| qpublic | fl_clay | parcel_id |
| qpublic | fl_dixie | parcel_id |
| beacon | in_gibson | tax_table |

### Appendix C: Complete Coverage Summary

**Total Platforms:** 27
**Config Types per Platform:** 7
**Total Config Files:** 27 × 7 = **189 files**

**Platform Coverage:**
- Tier 1 (HTML samples): 9 platforms — ✅ Complete
- Tier 2 (Existing parsers): 11 platforms — ✅ Complete
- Tier 3 (New from v2): 7 platforms — ✅ Complete
