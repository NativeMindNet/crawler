# Implementation Plan: Imagery & Photo Service

## Phase 1: Consolidation (Completed)
- [x] Extend `ParcelData` with `image_urls` and `google_maps_url`.
- [x] Implement `BaseParser.extract_images` for keyword-based image discovery.
- [x] Implement `ImageryService.enrich_with_external_links` for coordinate-based links.
- [x] Refactor all 10+ platform parsers to use unified logic.
- [x] Create `CustomGISParser` to unify fragmented Florida scrapers.

## Phase 2: Integration & Verification (Completed)
- [x] Integrate `finalize()` method in scrapers (`QPublic`, `FloridaTax`, `Beacon`).
- [x] Implement `tests/test_imagery_service.py` to verify:
    - Image extraction across different platform HTML samples.
    - Link generation correctness (coordinates to URLs).
    - Deduplication in `consolidate_images`.
- [x] Verify `CustomGISParser` against Custom GIS-style HTML (test_custom_gis_parser_extracts_images).

## Phase 3: Advanced Analysis (Partial)
- [ ] Implement `PropertyPhotoAnalyzer.analyze()` with actual YOLOv8 weights (placeholder remains).
- [x] Implement `SatelliteChangeDetector` pixel-comparison logic (PIL-based diff, configurable threshold).
- [x] Add `ImageryService.download_all(parcels, output_dir)` to batch fetch images for local analysis.
