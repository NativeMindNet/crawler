# Plan: Bulk Ingestion Module

**Version:** 0.1
**Status:** PLANNING PHASE
**Last Updated:** 2026-01-31

---

## Phase 1: Foundation & State Management
- [ ] Implement `IngestionState` class in `storage/ingestion.py`.
- [ ] Support `msgpack` for row index tracking.
- [ ] Implement file hashing for idempotency.

## Phase 2: Source Readers
- [ ] Implement `BaseReader` interface.
- [ ] Implement `CSVReader` using `csv.DictReader`.
- [ ] Implement `GISReader` using `geopandas`.
- [ ] Implement `ExcelReader` using `openpyxl`.

## Phase 3: Transformation Logic
- [ ] Implement `MappingProfile` loader and validator.
- [ ] Implement `Transformer` with standard functions (`clean_parcel_id`, `to_decimal`, etc.).
- [ ] Support "Constant" and "Composite" mapping types.

## Phase 4: Pipeline Orchestration
- [ ] Implement `BulkIngestionPipeline`.
- [ ] Integrate with `LocalPersistenceManager` to save results as JSON files and register in DB.
- [ ] Support batching (upsert every N rows).

## Phase 5: Verification & CLI
- [ ] Create a CLI tool `importer_bulk.py` to trigger ingestions.
- [ ] Add unit tests for `Transformer` and `Readers`.
- [ ] Integration test: Ingest a sample CSV and verify it appears in `results` table.

## Success Criteria
1. Successfully ingest 1000 rows from a CSV in < 10 seconds.
2. Interrupted ingestion resumes from the last successfully processed chunk.
3. GIS attributes and geometries are correctly extracted from Shapefiles.
4. Results are compatible with `sync.py` for Gateway upload.
