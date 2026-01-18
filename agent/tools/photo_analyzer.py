"""
Photo Analyzer Tool
Analyzes user-uploaded site photos using Claude Vision
"""

from typing import Dict, Any
import base64
import logging
import anthropic

from agent.tools.base_tool import BaseTool
from agent.config import settings

logger = logging.getLogger(__name__)


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
                "question": {
                    "type": "string",
                    "description": "Optional specific question about the site (e.g., 'Is this location sunny enough?')"
                }
            },
            "required": ["image_base64"]
        }

    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute photo analysis"""
        image_base64 = kwargs['image_base64']
        question = kwargs.get('question', '')

        # Validate image
        if not image_base64:
            raise ValueError("Image data is required")

        # Construct analysis prompt
        analysis_prompt = self._build_analysis_prompt(question)

        try:
            # Call Claude Vision API
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250514",  # Vision-enabled model
                max_tokens=2000,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "image",
                                "source": {
                                    "type": "base64",
                                    "media_type": "image/jpeg",
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

            # Parse the response (Claude will return structured text)
            # For simplicity, return the full analysis
            # In production, you might parse into structured JSON

            return {
                'analysis': analysis_text,
                'question_asked': question if question else 'General site analysis',
                'model_used': 'claude-sonnet-4-5',
                'suggestions': [
                    "Cross-reference this analysis with satellite data (NDVI, slope) for complete assessment",
                    "Take photos from multiple angles for comprehensive evaluation",
                    "Note time of day for accurate sunlight assessment"
                ]
            }

        except anthropic.APIError as e:
            logger.error(f"Claude Vision API error: {e}")
            raise

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
