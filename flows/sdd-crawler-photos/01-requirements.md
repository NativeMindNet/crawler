# Requirements - Parcel Photo Parsing Consolidation

## Objective
Consolidate parcel photo parsing and scraping logic from various existing flows into a unified, reusable module or service within `taxlien-parser`.

## Sources to Extract From
- `flows/sdd-miw-gift/`
- `flows/sdd-taxlien-parser/` (likely refers to `sdd-taxlien-parser-parcel` or general parser logic)
- `flows/sdd-taxlien-enrichment/`

## User Stories
- As a developer, I want a single place for parcel photo parsing so that I don't have to maintain duplicate logic.
- As a system, I want to be able to extract parcel photos from different platforms consistently.

## Functional Requirements
- Identify and extract photo parsing logic from `sdd-miw-gift`.
- Identify and extract photo parsing logic from `sdd-taxlien-parser` (general or specific sub-flows).
- Identify and extract photo parsing logic from `sdd-taxlien-enrichment`.
- Design a unified interface/service for photo parsing.

## Constraints
- Must integrate with the existing `taxlien-parser` architecture.
- Must handle different source platforms (e.g., qPublic, Beacon, etc.) if applicable.
