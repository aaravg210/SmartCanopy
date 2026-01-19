"""
Photo Analyzer Tool
Analyzes user-uploaded site photos using Claude Vision
"""

from typing import Dict, Any, Optional
import base64
import logging
import mimetypes
from pathlib import Path
import anthropic

from agent.tools.base_tool import BaseTool
from agent.config import settings

logger = logging.getLogger(__name__)

# Supported image types for Claude Vision
SUPPORTED_MEDIA_TYPES = {
    'image/jpeg': ['.jpg', '.jpeg'],
    'image/png': ['.png'],
    'image/gif': ['.gif'],
    'image/webp': ['.webp']
}


class PhotoAnalyzerTool(BaseTool):
    """
    Analyzes site photos using Claude Vision API

    Provides:
    - Site characteristics (dimensions, sunlight, soil)
    - Existing features (vegetation, hardscape, obstacles)
    - Suitability assessment
    - Recommendations for preparation
    """

    def __init__(self, api_key: str = None):
        super().__init__()
        self.client = anthropic.Anthropic(api_key=api_key or settings.anthropic_api_key)

    @property
    def name(self) -> str:
        return "photo_analyzer"

    @property
    def description(self) -> str:
        return (
            "Analyzes user-uploaded photos of planting sites using computer vision. "
            "Identifies site characteristics, obstacles, sunlight exposure, and provides "
            "suitability assessment with preparation recommendations."
        )

    @property
    def input_schema(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "image_base64": {
                    "type": "string",
                    "description": "Base64-encoded image of the planting site"
                },
                "image_path": {
                    "type": "string",
                    "description": "Path to an image file on disk (alternative to image_base64)"
                },
                "media_type": {
                    "type": "string",
                    "description": "Media type of the image (e.g., 'image/jpeg', 'image/png'). Auto-detected if not provided.",
                    "enum": ["image/jpeg", "image/png", "image/gif", "image/webp"]
                },
                "question": {
                    "type": "string",
                    "description": "Optional specific question about the site (e.g., 'Is this location sunny enough?')"
                }
            },
            "required": []
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute photo analysis"""
        image_base64 = kwargs.get('image_base64')
        image_path = kwargs.get('image_path')
        media_type = kwargs.get('media_type')
        question = kwargs.get('question', '')

        # Load image from path if provided
        if image_path and not image_base64:
            image_base64, media_type = self._load_image_from_path(image_path)
        elif not image_base64:
            raise ValueError("Either image_base64 or image_path is required")

        # Auto-detect media type if not provided
        if not media_type:
            media_type = self._detect_media_type(image_base64)

        # Validate media type
        if media_type not in SUPPORTED_MEDIA_TYPES:
            raise ValueError(
                f"Unsupported media type: {media_type}. "
                f"Supported types: {list(SUPPORTED_MEDIA_TYPES.keys())}"
            )

        # Construct analysis prompt
        analysis_prompt = self._build_analysis_prompt(question)

        try:
            # Call Claude Vision API - use sonnet for cost efficiency
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",  # Vision-enabled model
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": media_type,
                                    "data": image_base64
                                }
                            },
                            {
                                "type": "text",
                                "text": analysis_prompt
                            }
                        ]
                    }
                ]
            )

            # Extract response text
            analysis_text = response.content[0].text

            # Parse structured data from the analysis
            parsed_analysis = self._parse_analysis(analysis_text)

            return {
                'analysis': analysis_text,
                'parsed': parsed_analysis,
                'question_asked': question if question else 'General site analysis',
                'model_used': 'claude-sonnet-4',
                'media_type': media_type,
                'suggestions': [
                    "Cross-reference this analysis with satellite data (NDVI, slope) for complete assessment",
                    "Take photos from multiple angles for comprehensive evaluation",
                    "Note time of day for accurate sunlight assessment"
                ]
            }

        except anthropic.APIError as e:
            logger.error(f"Claude Vision API error: {e}")
            raise

    def _load_image_from_path(self, image_path: str) -> tuple[str, str]:
        """
        Load image from file path and return base64 data with media type.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (base64_data, media_type)

        Raises:
            ValueError: If file doesn't exist or is not a supported image type
        """
        path = Path(image_path)

        if not path.exists():
            raise ValueError(f"Image file not found: {image_path}")

        # Detect media type from extension
        suffix = path.suffix.lower()
        media_type = None
        for mtype, extensions in SUPPORTED_MEDIA_TYPES.items():
            if suffix in extensions:
                media_type = mtype
                break

        if not media_type:
            raise ValueError(
                f"Unsupported file extension: {suffix}. "
                f"Supported extensions: {[ext for exts in SUPPORTED_MEDIA_TYPES.values() for ext in exts]}"
            )

        # Read and encode the image
        with open(path, 'rb') as f:
            image_data = f.read()

        image_base64 = base64.b64encode(image_data).decode('utf-8')

        logger.info(f"Loaded image from {image_path} ({len(image_data)} bytes, {media_type})")

        return image_base64, media_type

    def _detect_media_type(self, image_base64: str) -> str:
        """
        Detect media type from base64 image data by examining magic bytes.

        Args:
            image_base64: Base64-encoded image data

        Returns:
            Detected media type (defaults to image/jpeg if unknown)
        """
        try:
            # Decode first few bytes to check magic numbers
            header = base64.b64decode(image_base64[:32])

            # Check magic bytes
            if header[:8] == b'\x89PNG\r\n\x1a\n':
                return 'image/png'
            elif header[:2] == b'\xff\xd8':
                return 'image/jpeg'
            elif header[:6] in (b'GIF87a', b'GIF89a'):
                return 'image/gif'
            elif header[:4] == b'RIFF' and header[8:12] == b'WEBP':
                return 'image/webp'
            else:
                logger.warning("Could not detect image type, defaulting to image/jpeg")
                return 'image/jpeg'
        except Exception as e:
            logger.warning(f"Error detecting media type: {e}, defaulting to image/jpeg")
            return 'image/jpeg'

    def _parse_analysis(self, analysis_text: str) -> Dict[str, Any]:
        """
        Parse the analysis text to extract structured information.

        Args:
            analysis_text: Raw analysis text from Claude

        Returns:
            Dictionary with parsed fields
        """
        parsed = {
            'suitability_rating': None,
            'sunlight_exposure': None,
            'recommended_tree_size': None,
            'key_concerns': [],
            'preparation_needed': []
        }

        analysis_lower = analysis_text.lower()

        # Extract suitability rating
        for rating in ['excellent', 'good', 'fair', 'poor']:
            if rating in analysis_lower:
                parsed['suitability_rating'] = rating
                break

        # Extract sunlight exposure
        if 'full sun' in analysis_lower:
            parsed['sunlight_exposure'] = 'full_sun'
        elif 'partial shade' in analysis_lower or 'partial sun' in analysis_lower:
            parsed['sunlight_exposure'] = 'partial_shade'
        elif 'full shade' in analysis_lower:
            parsed['sunlight_exposure'] = 'full_shade'

        # Extract recommended tree size
        for size in ['small', 'medium', 'large']:
            if f'{size} tree' in analysis_lower:
                parsed['recommended_tree_size'] = size
                break

        return parsed

    def _build_analysis_prompt(self, user_question: str = '') -> str:
        """Build the analysis prompt for Claude Vision"""
        base_prompt = """Analyze this planting site photo and provide a detailed assessment for tree planting.

Please evaluate:

1. **Site Dimensions & Space**
   - Approximate area available for planting
   - Spatial constraints or limitations
   - Recommended maximum tree size

2. **Sunlight Exposure**
   - Full sun, partial shade, or full shade
   - Evidence from shadows, existing vegetation
   - Time of day considerations

3. **Existing Features**
   - Current vegetation (grass, shrubs, trees)
   - Hardscape (pavement, structures, fences)
   - Obstacles or challenges
   - Soil visibility and condition indicators

4. **Site Conditions**
   - Soil type indicators (if visible)
   - Drainage indicators
   - Slope or terrain
   - Signs of compaction or disturbance

5. **Planting Suitability**
   - Overall suitability rating (excellent/good/fair/poor)
   - Best tree types for this site (small/medium/large, deciduous/evergreen)
   - Key concerns or challenges

6. **Preparation Recommendations**
   - Site preparation steps needed
   - Obstacles to remove or address
   - Soil amendments or improvements
   - Additional information needed

Please be specific and practical in your assessment."""

        if user_question:
            base_prompt += f"\n\nUser's specific question: {user_question}\n\nPlease address this question in your analysis."

        return base_prompt
