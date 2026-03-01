"""Tests for imagery service module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from crawler.imagery.link_generator import LinkGenerator
from crawler.imagery.downloader import ImageDownloader, DownloadResult
from crawler.imagery.service import ImageryService, ImageryResult
from crawler.imagery.analyzer import ImageAnalyzer, AnalysisResult, Detection
from crawler.models.external_links import ExternalLinks


class TestLinkGenerator:
    """Tests for LinkGenerator."""

    def test_generate_from_coords(self):
        """Test link generation from coordinates."""
        generator = LinkGenerator()
        result = generator.generate(latitude=33.7490, longitude=-84.3880)

        assert result.latitude == 33.7490
        assert result.longitude == -84.3880
        assert "33.7490" in result.google_maps
        assert "-84.3880" in result.google_maps
        assert result.google_street_view is not None
        assert result.bing_maps is not None
        assert result.apple_maps is not None

    def test_generate_from_address(self):
        """Test link generation from address."""
        generator = LinkGenerator()
        result = generator.generate(address="123 Main St, Atlanta, GA")

        assert result.address == "123 Main St, Atlanta, GA"
        assert "123+Main+St" in result.google_maps
        assert result.google_street_view is None  # Can't do street view without coords

    def test_generate_with_both(self):
        """Test link generation with both coords and address."""
        generator = LinkGenerator()
        result = generator.generate(
            latitude=33.7490,
            longitude=-84.3880,
            address="123 Main St",
        )

        assert result.latitude == 33.7490
        assert result.address == "123 Main St"
        assert "33.7490" in result.google_maps

    def test_generate_empty_returns_empty(self):
        """Test empty input returns empty ExternalLinks."""
        generator = LinkGenerator()
        result = generator.generate()

        assert result.latitude is None
        assert result.google_maps is None

    def test_zillow_link(self):
        """Test Zillow link generation."""
        generator = LinkGenerator()
        link = generator.generate_zillow_link("123 Main St, Atlanta")

        assert "zillow.com" in link
        assert "123+Main+St" in link

    def test_redfin_link(self):
        """Test Redfin link generation."""
        generator = LinkGenerator()
        link = generator.generate_redfin_link("123 Main St, Atlanta")

        assert "redfin.com" in link


class TestImageDownloader:
    """Tests for ImageDownloader."""

    @pytest.fixture
    def downloader(self, tmp_path):
        """Create downloader instance."""
        return ImageDownloader(
            output_dir=tmp_path,
            max_concurrent=2,
            max_size_mb=5.0,
            timeout=10.0,
        )

    def test_init(self, tmp_path):
        """Test downloader initialization."""
        downloader = ImageDownloader(output_dir=tmp_path)

        assert downloader.output_dir == tmp_path
        assert downloader.max_concurrent == 5
        assert downloader.max_retries == 3

    def test_get_filename_from_url(self, downloader):
        """Test filename extraction from URL."""
        url = "https://example.com/images/photo.jpg"
        filename = downloader.get_filename_from_url(url)

        assert filename == "photo.jpg"

    @pytest.mark.asyncio
    async def test_validate_url_invalid(self, downloader):
        """Test URL validation with invalid URL."""
        is_valid, error = await downloader.validate_url("https://invalid-url-test.example")

        assert is_valid is False
        assert error is not None


class TestImageAnalyzer:
    """Tests for ImageAnalyzer."""

    def test_init_placeholder_mode(self):
        """Test analyzer initializes in placeholder mode."""
        analyzer = ImageAnalyzer()

        assert analyzer.model is None
        assert analyzer.is_model_loaded() is False

    @pytest.mark.asyncio
    async def test_analyze_file_not_found(self, tmp_path):
        """Test analysis of non-existent file."""
        analyzer = ImageAnalyzer()
        result = await analyzer.analyze(tmp_path / "nonexistent.jpg")

        assert result.success is False
        assert "not found" in result.error

    @pytest.mark.asyncio
    async def test_analyze_placeholder_returns_success(self, tmp_path):
        """Test placeholder analysis returns success."""
        # Create a test image file
        test_image = tmp_path / "test.jpg"
        test_image.write_bytes(b"fake image data")

        analyzer = ImageAnalyzer()
        result = await analyzer.analyze(test_image)

        assert result.success is True
        assert result.property_features.get("analyzer_mode") == "placeholder"

    def test_extract_property_features(self):
        """Test property feature extraction from detections."""
        analyzer = ImageAnalyzer()
        detections = [
            Detection(label="pool", confidence=0.9),
            Detection(label="garage", confidence=0.85),
            Detection(label="car", confidence=0.8),
            Detection(label="car", confidence=0.75),
            Detection(label="tree", confidence=0.7),
        ]

        features = analyzer.extract_property_features(detections)

        assert features["has_pool"] is True
        assert features["has_garage"] is True
        assert features["vehicle_count"] == 2
        assert features["tree_count"] == 1


class TestImageryService:
    """Tests for ImageryService."""

    @pytest.fixture
    def service(self, tmp_path):
        """Create imagery service instance."""
        return ImageryService(
            output_dir=tmp_path,
            download_images=False,  # Disable for unit tests
            analyze_images=False,
        )

    @pytest.mark.asyncio
    async def test_process_generates_external_links(self, service):
        """Test process generates external links."""
        html = "<html><body><img src='test.jpg'></body></html>"

        result = await service.process(
            task_id="test-123",
            html=html,
            latitude=33.7490,
            longitude=-84.3880,
        )

        assert result.task_id == "test-123"
        assert result.external_links is not None
        assert result.external_links.latitude == 33.7490

    @pytest.mark.asyncio
    async def test_process_extracts_images(self, service):
        """Test process extracts image URLs."""
        html = """
        <html><body>
            <img src="property1.jpg">
            <img src="property2.png">
        </body></html>
        """

        result = await service.process(
            task_id="test-123",
            html=html,
        )

        assert len(result.extracted_urls) == 2

    @pytest.mark.asyncio
    async def test_process_filters_icons(self, service):
        """Test process filters out icon images."""
        html = """
        <html><body>
            <img src="property.jpg">
            <img src="icon-small.png">
            <img src="logo.png">
        </body></html>
        """

        result = await service.process(
            task_id="test-123",
            html=html,
        )

        # Should only get property.jpg, not icons/logos
        assert len(result.extracted_urls) == 1
        assert "property.jpg" in result.extracted_urls[0]

    @pytest.mark.asyncio
    async def test_process_limits_images(self, tmp_path):
        """Test process respects max_images limit."""
        service = ImageryService(
            output_dir=tmp_path,
            download_images=False,
            max_images=2,
        )

        html = """
        <html><body>
            <img src="img1.jpg">
            <img src="img2.jpg">
            <img src="img3.jpg">
            <img src="img4.jpg">
        </body></html>
        """

        result = await service.process(
            task_id="test-123",
            html=html,
        )

        assert len(result.extracted_urls) <= 2

    def test_generate_links_only(self, service):
        """Test generating links without processing HTML."""
        links = service.generate_links_only(
            latitude=33.7490,
            longitude=-84.3880,
            address="123 Main St",
        )

        assert links.latitude == 33.7490
        assert links.google_maps is not None


class TestImageryResult:
    """Tests for ImageryResult dataclass."""

    def test_success_count(self):
        """Test success_count property."""
        result = ImageryResult(
            task_id="test",
            downloaded=[
                DownloadResult(url="a.jpg", success=True),
                DownloadResult(url="b.jpg", success=True),
                DownloadResult(url="c.jpg", success=False, error="Failed"),
            ],
        )

        assert result.success_count == 2
        assert result.failed_count == 1

    def test_to_dict(self):
        """Test conversion to dictionary."""
        result = ImageryResult(
            task_id="test-123",
            external_links=ExternalLinks(latitude=33.0, longitude=-84.0),
            extracted_urls=["a.jpg", "b.jpg"],
        )

        data = result.to_dict()

        assert data["task_id"] == "test-123"
        assert data["external_links"]["latitude"] == "33.0"
        assert len(data["extracted_urls"]) == 2


class TestDetection:
    """Tests for Detection dataclass."""

    def test_to_dict(self):
        """Test detection to_dict."""
        det = Detection(
            label="house",
            confidence=0.95,
            bbox=[10, 20, 100, 200],
        )

        data = det.to_dict()

        assert data["label"] == "house"
        assert data["confidence"] == 0.95
        assert data["bbox"] == [10, 20, 100, 200]


class TestAnalysisResult:
    """Tests for AnalysisResult dataclass."""

    def test_to_dict(self, tmp_path):
        """Test analysis result to_dict."""
        result = AnalysisResult(
            image_path=tmp_path / "test.jpg",
            success=True,
            detections=[Detection(label="house", confidence=0.9)],
            labels=["house"],
        )

        data = result.to_dict()

        assert data["success"] is True
        assert len(data["detections"]) == 1
        assert data["labels"] == ["house"]
