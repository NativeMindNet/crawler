"""GIS source reader (Shapefile/GeoJSON)."""

from typing import Iterator, Dict, Any, List
import json

from crawler.bulk.readers.base import SourceReader


class GISReader(SourceReader):
    """
    Reader for GIS files (Shapefile, GeoJSON).
    
    Features:
    - Shapefile support via geopandas
    - GeoJSON native support
    - Coordinate extraction
    - Geometry handling
    """

    def __init__(
        self,
        file_path: str,
        format: str = "auto",
    ):
        super().__init__(file_path)
        self.format = format  # "shapefile", "geojson", "auto"
        self._data = None
        self._detect_format()

    def _detect_format(self) -> None:
        """Detect file format."""
        if self.format != "auto":
            return

        ext = self.file_path.suffix.lower()
        if ext == ".json" or ext == ".geojson":
            self.format = "geojson"
        elif ext == ".shp":
            self.format = "shapefile"
        else:
            # Try to detect by content
            try:
                with open(self.file_path, "r") as f:
                    first_char = f.read(1)
                    if first_char in ["{", "["]:
                        self.format = "geojson"
            except:
                self.format = "geojson"  # Default

    def _load_data(self) -> None:
        """Load GIS data."""
        if self._data is not None:
            return

        if self.format == "geojson":
            with open(self.file_path, "r") as f:
                self._data = json.load(f)
        elif self.format == "shapefile":
            try:
                import geopandas as gpd
                self._data = gpd.read_file(self.file_path)
            except ImportError:
                raise ImportError("geopandas required for Shapefile support")

    def get_row_count(self) -> int:
        """Count features in GIS file."""
        self._load_data()

        if self.format == "geojson":
            return len(self._data.get("features", []))
        elif self.format == "shapefile":
            return len(self._data)
        return 0

    def read_rows(self, batch_size: int = 100) -> Iterator[Dict[str, Any]]:
        """Read features from GIS file."""
        self._load_data()

        if self.format == "geojson":
            yield from self._read_geojson(batch_size)
        elif self.format == "shapefile":
            yield from self._read_shapefile(batch_size)

    def _read_geojson(self, batch_size: int) -> Iterator[Dict[str, Any]]:
        """Read GeoJSON features."""
        features = self._data.get("features", [])
        batch = []

        for feature in features:
            # Convert feature to flat dict
            row = feature.get("properties", {}).copy()

            # Add geometry info
            geometry = feature.get("geometry", {})
            if geometry.get("type") == "Point":
                coords = geometry.get("coordinates", [])
                if len(coords) >= 2:
                    row["longitude"] = coords[0]
                    row["latitude"] = coords[1]

            # Add feature ID
            if feature.get("id"):
                row["feature_id"] = feature["id"]

            batch.append(row)

            if len(batch) >= batch_size:
                yield from batch
                batch = []

        if batch:
            yield from batch

    def _read_shapefile(self, batch_size: int) -> Iterator[Dict[str, Any]]:
        """Read Shapefile records."""
        batch = []

        for idx, row in self._data.iterrows():
            row_dict = {}

            # Convert each column
            for col in self._data.columns:
                if col == "geometry":
                    # Extract centroid coordinates
                    geom = row[col]
                    if geom and geom.centroid:
                        row_dict["longitude"] = geom.centroid.x
                        row_dict["latitude"] = geom.centroid.y
                else:
                    row_dict[col] = row[col]

            batch.append(row_dict)

            if len(batch) >= batch_size:
                yield from batch
                batch = []

        if batch:
            yield from batch

    def get_columns(self) -> List[str]:
        """Get field names from GIS file."""
        self._load_data()

        if self.format == "geojson":
            features = self._data.get("features", [])
            if features:
                return list(features[0].get("properties", {}).keys())
        elif self.format == "shapefile":
            return list(self._data.columns)

        return []

    def validate(self) -> tuple[bool, list]:
        """Validate GIS file."""
        errors = []

        try:
            self._load_data()

            if self.get_row_count() == 0:
                errors.append("GIS file has no features")

        except Exception as e:
            errors.append(f"Failed to read GIS file: {e}")

        return len(errors) == 0, errors
