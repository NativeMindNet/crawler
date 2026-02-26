# Requirements: sdd-taxlien-parser-configs

## Overview
Standardize and centralize all platform-specific configurations directly within the `platforms/{platform_name}/` directory.

## Directory Structure
```text
platforms/{platform_name}/
├── scraper.py          # Network logic
├── parser.py           # Extraction logic
├── manifest.json       # Technical specs (Rate limits, Cloudflare, Proxy)
├── counties.json       # County-to-Platform mapping (AppID, params, Tier1 status)
├── selectors.json      # DOM Selectors (CSS/XPath)
├── mapping.json        # Field mapping to Standard Schema
├── business_rules.json # Normalization, date formats, etc.
├── schedule.json       # Update frequency and auction dates
└── discovery.json      # URL patterns and ID validation rules
```

## Functional Requirements
1. **Flat Structure**: Configuration files must reside in the root of the platform directory, not in a subfolder.
2. **Standardization**: Use JSON for all data files to ensure consistency across the project.
3. **Multi-level Configuration (Inheritance)**: Support a "Default + Overrides" model within JSON files.
    - `default`: Common settings for the entire platform.
    - `overrides`: County-specific values that supersede defaults (keyed by `county_key`).
4. **Data Extraction**: Extract selectors from legacy `.js` files and county data from `tier1_config.py`.
5. **Platform Autonomy**: Each platform directory must contain everything needed to scrape and parse that platform.
6. **Complete Selector Coverage**: All platforms in `/platforms/` must have populated `selectors.json` and `mapping.json` files.
7. **Alignment with Sample Collectors**: Platforms specified in `sdd-platforms-sample-collector` and `sdd-platforms-sample-collector-v2` must have corresponding configs.

## Acceptance Criteria
- [ ] Each active platform directory contains the 7 standard JSON files.
- [ ] `auto_config.json` is migrated to `counties.json`.
- [ ] `tier1_config.py` data is distributed into platform-specific `counties.json`.
- [ ] No hardcoded configuration values remain in the implementation code.
- [ ] **NEW**: All 20 platforms in `/platforms/` have populated `selectors.json` (non-empty, >100 bytes).
- [ ] **NEW**: All 20 platforms in `/platforms/` have populated `mapping.json` (non-empty, >100 bytes).
- [ ] **NEW**: Platforms from `sdd-platforms-sample-collector-v2` with CRITICAL/HIGH priority have configs (kofile, cott_systems, mytaxbill, vgsi, avitar, nh_tax_kiosk).
- [ ] **NEW**: Selectors are validated against real HTML samples from `taxlien-storage/`.

## Platform Coverage Requirements

### Tier 1: Existing platforms with HTML samples (MUST HAVE)
| Platform | HTML Samples | Status |
|----------|--------------|--------|
| custom_gis | 709 | ✅ Complete |
| qpublic | 133 | ✅ Complete |
| beacon | 70 | ✅ Complete |
| tyler | 5 | ✅ Complete |
| arcgis | 2 | ✅ Complete |
| netronline | 1 | ✅ Complete |

### Tier 2: Existing platforms without configs (HIGH PRIORITY)
| Platform | In Specs | In V2 | Priority |
|----------|----------|-------|----------|
| fidlar | ❌ | ✅ MEDIUM | ⚠️ |
| governmax | ✅ | ❌ | ⚠️ |
| bid4assets | ❌ | ❌ | 🟡 |
| cama | ❌ | ❌ | 🟡 |
| civic_source | ❌ | ❌ | 🟡 |
| egov | ❌ | ❌ | 🟡 |
| greenwoodmap | ❌ | ❌ | 🟡 |
| kcsgis | ❌ | ❌ | 🟡 |
| propertymax | ❌ | ❌ | 🟡 |
| alabamagis | ❌ | ❌ | 🟡 |
| tyler_technologies | ❌ | ❌ | 🟡 |

### Tier 3: New platforms from v2 (CRITICAL/HIGH)
| Platform | Data Type | Priority | Action |
|----------|-----------|----------|--------|
| kofile | Documents | CRITICAL | Create platform dir + configs |
| cott_systems | Documents | CRITICAL | Create platform dir + configs |
| mytaxbill | Taxes | CRITICAL | Create platform dir + configs |
| vgsi | Parcels | CRITICAL | Create platform dir + configs |
| avitar | Parcels | HIGH | Create platform dir + configs |
| nh_tax_kiosk | Taxes | HIGH | Create platform dir + configs |
| searchiqs | Documents | HIGH | Create platform dir + configs |

## Non-Goals
- Refactoring existing parser logic (selectors are extracted, not logic)
- Changing the ParcelData standard schema
- Modifying taxlien-storage HTML samples