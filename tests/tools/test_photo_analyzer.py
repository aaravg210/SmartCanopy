"""
Unit tests for PhotoAnalyzerTool
"""

import pytest
import base64
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from agent.tools.photo_analyzer import PhotoAnalyzerTool, SUPPORTED_MEDIA_TYPES


# Test image data - minimal valid images for each format
# 1x1 white pixel PNG
PNG_BYTES = bytes([
    0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A,  # PNG signature
    0x00, 0x00, 0x00, 0x0D, 0x49, 0x48, 0x44, 0x52,  # IHDR chunk
    0x00, 0x00, 0x00, 0x01, 0x00, 0x00, 0x00, 0x01,
    0x08, 0x02, 0x00, 0x00, 0x00, 0x90, 0x77, 0x53,
    0xDE, 0x00, 0x00, 0x00, 0x0C, 0x49, 0x44, 0x41,
    0x54, 0x08, 0xD7, 0x63, 0xF8, 0xFF, 0xFF, 0x3F,
    0x00, 0x05, 0xFE, 0x02, 0xFE, 0xDC, 0xCC, 0x59,
    0xE7, 0x00, 0x00, 0x00, 0x00, 0x49, 0x45, 0x4E,
    0x44, 0xAE, 0x42, 0x60, 0x82
])

# Minimal JPEG header (not a complete image but enough for detection)
JPEG_BYTES = bytes([0xFF, 0xD8, 0xFF, 0xE0, 0x00, 0x10, 0x4A, 0x46, 0x49, 0x46])

# GIF header
GIF_BYTES = b'GIF89a\x01\x00\x01\x00\x00\x00\x00;'

# WEBP header (minimal RIFF structure)
WEBP_BYTES = b'RIFF\x00\x00\x00\x00WEBPVP8 '


class TestPhotoAnalyzerToolMetadata:
    """Test tool metadata and schema"""

    def test_tool_name(self):
        """Test tool name is correct"""
        tool = PhotoAnalyzerTool()
        assert tool.name == "photo_analyzer"

    def test_tool_description(self):
        """Test description contains key information"""
        tool = PhotoAnalyzerTool()
        desc_lower = tool.description.lower()
        assert "photo" in desc_lower or "image" in desc_lower
        assert "site" in desc_lower or "planting" in desc_lower

    def test_input_schema_structure(self):
        """Test input schema has expected properties"""
        tool = PhotoAnalyzerTool()
        schema = tool.input_schema

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "image_base64" in schema["properties"]
        assert "image_path" in schema["properties"]
        assert "media_type" in schema["properties"]
        assert "question" in schema["properties"]

    def test_input_schema_media_type_enum(self):
        """Test media_type has correct enum values"""
        tool = PhotoAnalyzerTool()
        media_type_schema = tool.input_schema["properties"]["media_type"]

        assert "enum" in media_type_schema
        assert set(media_type_schema["enum"]) == set(SUPPORTED_MEDIA_TYPES.keys())


class TestMediaTypeDetection:
    """Test automatic media type detection"""

    def test_detect_png(self):
        """Test PNG detection from magic bytes"""
        tool = PhotoAnalyzerTool()
        image_base64 = base64.b64encode(PNG_BYTES).decode('utf-8')
        detected = tool._detect_media_type(image_base64)
        assert detected == 'image/png'

    def test_detect_jpeg(self):
        """Test JPEG detection from magic bytes"""
        tool = PhotoAnalyzerTool()
        image_base64 = base64.b64encode(JPEG_BYTES).decode('utf-8')
        detected = tool._detect_media_type(image_base64)
        assert detected == 'image/jpeg'

    def test_detect_gif(self):
        """Test GIF detection from magic bytes"""
        tool = PhotoAnalyzerTool()
        image_base64 = base64.b64encode(GIF_BYTES).decode('utf-8')
        detected = tool._detect_media_type(image_base64)
        assert detected == 'image/gif'

    def test_detect_webp(self):
        """Test WEBP detection from magic bytes"""
        tool = PhotoAnalyzerTool()
        image_base64 = base64.b64encode(WEBP_BYTES).decode('utf-8')
        detected = tool._detect_media_type(image_base64)
        assert detected == 'image/webp'

    def test_detect_unknown_defaults_to_jpeg(self):
        """Test unknown format defaults to JPEG"""
        tool = PhotoAnalyzerTool()
        unknown_bytes = b'\x00\x01\x02\x03\x04\x05\x06\x07'
        image_base64 = base64.b64encode(unknown_bytes).decode('utf-8')
        detected = tool._detect_media_type(image_base64)
        assert detected == 'image/jpeg'


class TestImageLoading:
    """Test loading images from file paths"""

    def test_load_png_from_path(self, tmp_path):
        """Test loading PNG file"""
        tool = PhotoAnalyzerTool()

        # Create temp PNG file
        png_file = tmp_path / "test.png"
        png_file.write_bytes(PNG_BYTES)

        image_base64, media_type = tool._load_image_from_path(str(png_file))

        assert media_type == 'image/png'
        assert base64.b64decode(image_base64) == PNG_BYTES

    def test_load_jpeg_from_path(self, tmp_path):
        """Test loading JPEG file"""
        tool = PhotoAnalyzerTool()

        # Create temp JPEG file
        jpg_file = tmp_path / "test.jpg"
        jpg_file.write_bytes(JPEG_BYTES)

        image_base64, media_type = tool._load_image_from_path(str(jpg_file))

        assert media_type == 'image/jpeg'
        assert base64.b64decode(image_base64) == JPEG_BYTES

    def test_load_file_not_found(self, tmp_path):
        """Test error when file doesn't exist"""
        tool = PhotoAnalyzerTool()

        with pytest.raises(ValueError, match="not found"):
            tool._load_image_from_path(str(tmp_path / "nonexistent.png"))

    def test_load_unsupported_extension(self, tmp_path):
        """Test error for unsupported file extension"""
        tool = PhotoAnalyzerTool()

        # Create temp file with unsupported extension
        bmp_file = tmp_path / "test.bmp"
        bmp_file.write_bytes(b'BM test data')

        with pytest.raises(ValueError, match="Unsupported file extension"):
            tool._load_image_from_path(str(bmp_file))


class TestAnalysisParsing:
    """Test parsing of analysis results"""

    def test_parse_excellent_rating(self):
        """Test parsing excellent suitability rating"""
        tool = PhotoAnalyzerTool()
        text = "The site has excellent conditions for tree planting."
        parsed = tool._parse_analysis(text)
        assert parsed['suitability_rating'] == 'excellent'

    def test_parse_good_rating(self):
        """Test parsing good suitability rating"""
        tool = PhotoAnalyzerTool()
        text = "Overall, this is a good location."
        parsed = tool._parse_analysis(text)
        assert parsed['suitability_rating'] == 'good'

    def test_parse_fair_rating(self):
        """Test parsing fair suitability rating"""
        tool = PhotoAnalyzerTool()
        text = "The site offers fair conditions."
        parsed = tool._parse_analysis(text)
        assert parsed['suitability_rating'] == 'fair'

    def test_parse_poor_rating(self):
        """Test parsing poor suitability rating"""
        tool = PhotoAnalyzerTool()
        text = "Unfortunately, conditions are poor."
        parsed = tool._parse_analysis(text)
        assert parsed['suitability_rating'] == 'poor'

    def test_parse_full_sun(self):
        """Test parsing full sun exposure"""
        tool = PhotoAnalyzerTool()
        text = "The location receives full sun throughout the day."
        parsed = tool._parse_analysis(text)
        assert parsed['sunlight_exposure'] == 'full_sun'

    def test_parse_partial_shade(self):
        """Test parsing partial shade exposure"""
        tool = PhotoAnalyzerTool()
        text = "This area has partial shade from nearby buildings."
        parsed = tool._parse_analysis(text)
        assert parsed['sunlight_exposure'] == 'partial_shade'

    def test_parse_full_shade(self):
        """Test parsing full shade exposure"""
        tool = PhotoAnalyzerTool()
        text = "The site is in full shade under dense tree cover."
        parsed = tool._parse_analysis(text)
        assert parsed['sunlight_exposure'] == 'full_shade'

    def test_parse_tree_size_small(self):
        """Test parsing small tree recommendation"""
        tool = PhotoAnalyzerTool()
        text = "Due to space constraints, a small tree would be best."
        parsed = tool._parse_analysis(text)
        assert parsed['recommended_tree_size'] == 'small'

    def test_parse_tree_size_medium(self):
        """Test parsing medium tree recommendation"""
        tool = PhotoAnalyzerTool()
        text = "A medium tree would fit well in this space."
        parsed = tool._parse_analysis(text)
        assert parsed['recommended_tree_size'] == 'medium'

    def test_parse_tree_size_large(self):
        """Test parsing large tree recommendation"""
        tool = PhotoAnalyzerTool()
        text = "There's room for a large tree to mature."
        parsed = tool._parse_analysis(text)
        assert parsed['recommended_tree_size'] == 'large'


class TestPromptBuilding:
    """Test analysis prompt construction"""

    def test_base_prompt_includes_key_sections(self):
        """Test base prompt includes all evaluation sections"""
        tool = PhotoAnalyzerTool()
        prompt = tool._build_analysis_prompt()

        assert "Site Dimensions" in prompt
        assert "Sunlight Exposure" in prompt
        assert "Existing Features" in prompt
        assert "Site Conditions" in prompt
        assert "Planting Suitability" in prompt
        assert "Preparation Recommendations" in prompt

    def test_prompt_includes_user_question(self):
        """Test user question is appended to prompt"""
        tool = PhotoAnalyzerTool()
        question = "Is there enough space for an oak tree?"
        prompt = tool._build_analysis_prompt(question)

        assert question in prompt
        assert "User's specific question" in prompt

    def test_prompt_without_question(self):
        """Test prompt works without user question"""
        tool = PhotoAnalyzerTool()
        prompt = tool._build_analysis_prompt()

        assert "User's specific question" not in prompt


@pytest.mark.asyncio
class TestPhotoAnalyzerExecution:
    """Test execute method with mocked API"""

    async def test_execute_with_base64(self):
        """Test execution with base64 image data"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Site shows good conditions with full sun exposure. A medium tree would work well here.")]

        with patch.object(PhotoAnalyzerTool, '__init__', lambda x, api_key=None: None):
            tool = PhotoAnalyzerTool()
            tool.client = MagicMock()
            tool.client.messages.create.return_value = mock_response

            image_base64 = base64.b64encode(PNG_BYTES).decode('utf-8')
            result = await tool.execute(image_base64=image_base64)

            assert 'analysis' in result
            assert 'parsed' in result
            assert result['parsed']['suitability_rating'] == 'good'
            assert result['parsed']['sunlight_exposure'] == 'full_sun'
            assert result['media_type'] == 'image/png'
            assert result['model_used'] == 'claude-sonnet-4'

    async def test_execute_with_file_path(self, tmp_path):
        """Test execution with file path"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Excellent site for planting.")]

        # Create temp file
        png_file = tmp_path / "test.png"
        png_file.write_bytes(PNG_BYTES)

        with patch.object(PhotoAnalyzerTool, '__init__', lambda x, api_key=None: None):
            tool = PhotoAnalyzerTool()
            tool.client = MagicMock()
            tool.client.messages.create.return_value = mock_response

            result = await tool.execute(image_path=str(png_file))

            assert 'analysis' in result
            assert result['parsed']['suitability_rating'] == 'excellent'

    async def test_execute_with_explicit_media_type(self):
        """Test execution with explicitly specified media type"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Good conditions observed.")]

        with patch.object(PhotoAnalyzerTool, '__init__', lambda x, api_key=None: None):
            tool = PhotoAnalyzerTool()
            tool.client = MagicMock()
            tool.client.messages.create.return_value = mock_response

            image_base64 = base64.b64encode(JPEG_BYTES).decode('utf-8')
            result = await tool.execute(
                image_base64=image_base64,
                media_type='image/jpeg'
            )

            assert result['media_type'] == 'image/jpeg'

    async def test_execute_with_question(self):
        """Test execution with user question"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Yes, there is enough sunlight for a fruit tree.")]

        with patch.object(PhotoAnalyzerTool, '__init__', lambda x, api_key=None: None):
            tool = PhotoAnalyzerTool()
            tool.client = MagicMock()
            tool.client.messages.create.return_value = mock_response

            image_base64 = base64.b64encode(PNG_BYTES).decode('utf-8')
            question = "Is there enough sunlight for a fruit tree?"
            result = await tool.execute(
                image_base64=image_base64,
                question=question
            )

            assert result['question_asked'] == question

    async def test_execute_no_image_raises_error(self):
        """Test that execute raises error when no image provided"""
        tool = PhotoAnalyzerTool()

        with pytest.raises(ValueError, match="Either image_base64 or image_path is required"):
            await tool.execute()

    async def test_execute_unsupported_media_type_raises_error(self):
        """Test that unsupported media type raises error"""
        with patch.object(PhotoAnalyzerTool, '__init__', lambda x, api_key=None: None):
            tool = PhotoAnalyzerTool()

            image_base64 = base64.b64encode(PNG_BYTES).decode('utf-8')

            with pytest.raises(ValueError, match="Unsupported media type"):
                await tool.execute(
                    image_base64=image_base64,
                    media_type='image/bmp'
                )

    async def test_result_structure(self):
        """Test that result has expected structure"""
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Fair conditions with partial shade.")]

        with patch.object(PhotoAnalyzerTool, '__init__', lambda x, api_key=None: None):
            tool = PhotoAnalyzerTool()
            tool.client = MagicMock()
            tool.client.messages.create.return_value = mock_response

            image_base64 = base64.b64encode(PNG_BYTES).decode('utf-8')
            result = await tool.execute(image_base64=image_base64)

            # Check all expected fields
            assert 'analysis' in result
            assert 'parsed' in result
            assert 'question_asked' in result
            assert 'model_used' in result
            assert 'media_type' in result
            assert 'suggestions' in result
            assert isinstance(result['suggestions'], list)


@pytest.mark.requires_api_key
@pytest.mark.asyncio
class TestPhotoAnalyzerIntegration:
    """Integration tests that require actual API key"""

    async def test_analyze_real_image(self):
        """Test with a real image from test_data (requires API key)"""
        test_image_path = Path("test_data/Central_Park_New_York_NY_rgb.png")

        if not test_image_path.exists():
            pytest.skip("Test image not found")

        tool = PhotoAnalyzerTool()
        result = await tool.execute(image_path=str(test_image_path))

        assert 'analysis' in result
        assert len(result['analysis']) > 100  # Should have substantial analysis
        assert result['media_type'] == 'image/png'
