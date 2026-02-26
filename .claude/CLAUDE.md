# Sub-Project Context: Taxlien Parser Platform Configs

## Role
Это **Sub-Project** (Слой реализации taxlien-parser). Здесь ведется работа над конфигурациями платформ и парсерами.

## Workflow: Specs-as-Source Approach

### Core Principle
**Specifications are the single source of truth.** All platform selectors and mappings are defined in specification documents first, then generated into implementation files.

### Specification Hierarchy
1. **Consolidated Spec:** `flows/sdd-taxlien-parser-platforms-configs/03-specifications-consolidated.md`
   - Contains ALL platform selectors and mappings (27 platforms)
   - This is the authoritative reference
   - Changes start here, then propagate to `platforms/*/` JSON files

2. **Platform Config Files:** `platforms/{name}/selectors.json`, `mapping.json`
   - Generated from specification
   - Derived artifacts (not source of truth)
   - Used by runtime parsers

### SDD Flow
- Use `/sdd resume [name]` to continue existing spec flows
- Use `/sdd start [name]` for new features/changes
- Always update specs BEFORE modifying implementation code

### Working with Platform Configs
1. **Adding new selector:** First add to `03-specifications-consolidated.md`, then generate to `platforms/{name}/selectors.json`
2. **Modifying mapping:** First update spec document, then update JSON file
3. **New platform:** Create spec section first, then create platform directory with JSON files

## Implementation Targets
- **Tech:** Python, BeautifulSoup, CSS Selectors, JSON configs
- **Platforms:** 27 platforms (Tier 1, 2, 3)
- **Configs:** selectors.json, mapping.json, manifest.json, counties.json, business_rules.json, schedule.json, discovery.json

## Key Artifacts
- `flows/sdd-taxlien-parser-platforms-configs/03-specifications-consolidated.md` — Complete spec reference
- `platforms/` — Platform-specific config directories
- `parsers/platforms/` — Parser implementations
