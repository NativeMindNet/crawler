# Requirements: Bulk Ingestion Module

**Version:** 0.1
**Status:** REQUIREMENTS PHASE
**Last Updated:** 2026-01-31

---

## 1. Goal
Create a dedicated pipeline for ingesting large, static datasets (Bulk Data) such as Tax Rolls, GIS Shapefiles, and FTP dumps. This module bypasses the web crawling logic (Strategy/Scraper) and feeds directly into the storage layer (LPM).

## 2. User Stories

### US-1: GIS Import
**As a** data engineer
**I want** to upload a county's GIS Shapefile (.shp) containing 50,000 parcels
**So that** I can instantly populate the DB with Parcel IDs and geometries without crawling.

### US-2: Tax Roll CSV
**As a** researcher
**I want** to import a "Tax Roll Export" CSV file obtained from a county clerk
**So that** I can bulk-update tax statuses for an entire county.

### US-3: Format Normalization
**As a** system
**I want** to normalize different input columns (e.g., "PIN", "ParcelID", "MapNumber") into a standard `parcel_id`
**So that** the data is consistent with the rest of the platform.

## 3. Functional Requirements

### FR-0: Targeted Platforms & Coverage
The module MUST support existing bulk export formats identified:
- **RealAuction (CSV)**: Priority. Support for "Bid Upload" templates.
    - Coverage: ~15 FL counties (Columbia, Dixie, etc.), ~15 AZ counties (Apache, Pima, etc.).
- **Beacon (Schneider Corp)**: Support for "Export" functionality.
    - Coverage: 90 counties (e.g., FL-Calhoun, KS-Lyon).
- **qPublic (Schneider Corp)**: Support for "Export" functionality.
    - Coverage: 229 counties (e.g., FL-Alachua, GA-Chatham).

### FR-1: Supported Formats
The module MUST support:
- **CSV / Excel**: Standard tabular data (streaming for large files).
- **GIS Formats**: Shapefile (.shp), GeoJSON. Support for geometry (latitude/longitude) extraction.
- **JSON / JSONL**: Bulk JSON exports or line-delimited JSON.

### FR-2: State Management & Persistence
The pipeline MUST implement a reliable state tracking system to allow resumption and auditing:
- **Intermediate Storage**: Use a tiered approach:
    - `msgpack`: For high-performance binary serialization of large raw datasets.
    - `pickle`: For complex Python object state (e.g., partial mapping results).
    - `JSON`: For human-readable configuration and final summaries.
- **Resumption**: The system MUST track progress at the row/chunk level to allow resuming interrupted jobs.

### FR-3: Mapping Configuration (Profiles)
- Users MUST be able to define a "Mapping Profile" (JSON) for each source.
- Profiles should support:
    - **Direct Mapping**: `source_col` -> `target_field`.
    - **Constant Values**: Assign a fixed value (e.g., `state` = "FL") if missing in source.
    - **Transformations**: Simple expressions or pre-defined functions (e.g., `to_decimal`, `to_date`, `clean_parcel_id`).
    - **Composite Fields**: Concatenate multiple source columns into one target field.

### FR-4: Ingestion Pipeline
1. **Discovery**: Identify files in a source directory.
2. **Schema Inference (Optional)**: Suggest a mapping based on header similarity.
3. **Execution**:
    - Stream source file.
    - Apply mapping profile.
    - Validate required fields (`parcel_id`, `county`, `state`).
    - Upsert to DB using existing `DatabaseConnection` logic.

### FR-5: Idempotency & Upsert
- Re-importing the same file SHOULD NOT create duplicates.
- Existing records SHOULD be updated (Upsert) based on `parcel_id`, `county`, `state`.

### FR-6: Error Handling & Logging
- Log rows that failed validation or transformation.
- Continue processing the rest of the file on individual row errors.

## 4. Constraints
- Must use `LocalPersistenceManager` (LPM) for storage.
- Must handle large files (stream processing preferred for >1GB files).
- Must adhere to the tiered state management mandate (Pickle/JSON/Msgpack).
