# Specifications: Imagery & Photo Service

## 1. ImageryService Interface

The `ImageryService` is responsible for consolidating property photos and generating external mapping links.

### Data Model Enrichment
All `ParcelData` objects must be passed through `ImageryService.enrich_with_external_links()` to populate the following:
- `google_maps_url`: Direct link to Google Maps with Satellite view enabled.
- `metadata['street_view_url']`: Direct link to Google Street View at the property coordinates.
- `metadata['satellite_url']`: Direct link to Google Earth Web.
- `metadata['bing_maps_url']`: Direct link to Bing Maps Bird's Eye view.

### Property Photo Extraction
Platform parsers must use `BaseParser.extract_images(soup)` to:
- Identify `<img>` tags related to property photos.
- Filter out small icons, logos, and UI markers.
- Deduplicate URLs.
- Store results in `image_urls` (list of strings).

## 2. Platform Parsers Coverage

The following parsers are updated to support the unified imagery extraction:
- **Assessor/GIS Platforms**: Beacon, QPublic, ActData, ArCountyData, CustomGIS.
- **Tax Platforms**: FloridaTax, County-Taxes, GovernMax.
- **Recorder Platforms**: MyFloridaCounty, USLandRecords, Fidlar.

## 3. Advanced Features (Placeholders)

### 🕐 Historical Street View Timeline
Logic to generate URLs for specific historical years when supported by Google Maps URL parameters.

### 🛰️ Satellite Change Detection
Placeholder `detect_satellite_changes(parcel_id, years)` for future integration with CV models to detect:
- Roofline changes (new construction/additions).
- Pool installation.
- Significant debris or yard changes.

### 🏠 PropertyPhotoAnalyzer (YOLO)
Placeholder specifications for local YOLOv8 analysis of downloaded photos:
- Classes: `roof_damage`, `broken_window`, `boarded_up`, `overgrown_yard`, `debris`.
- Target: Automate the "condition score" for ML models.
