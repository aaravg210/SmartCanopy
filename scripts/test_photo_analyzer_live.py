#!/usr/bin/env python
"""
Live test script for PhotoAnalyzerTool using actual API.

Usage:
    python scripts/test_photo_analyzer_live.py [image_path]

If no image path is provided, uses the Central Park test image.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.tools.photo_analyzer import PhotoAnalyzerTool


async def test_photo_analysis(image_path: str = None):
    """Run photo analysis on an image"""

    # Default to test image
    if not image_path:
        image_path = "test_data/Central_Park_New_York_NY_rgb.png"

    path = Path(image_path)
    if not path.exists():
        print(f"Error: Image file not found: {image_path}")
        return

    print(f"Analyzing image: {image_path}")
    print(f"File size: {path.stat().st_size / 1024:.1f} KB")
    print("-" * 60)

    try:
        tool = PhotoAnalyzerTool()

        # Test 1: General analysis
        print("\n1. Running general site analysis...")
        result = await tool.execute(image_path=str(path))

        print(f"\nMedia type: {result['media_type']}")
        print(f"Question asked: {result['question_asked']}")
        print(f"Model used: {result['model_used']}")

        print("\n--- Parsed Results ---")
        for key, value in result['parsed'].items():
            print(f"  {key}: {value}")

        print("\n--- Full Analysis ---")
        print(result['analysis'])

        print("\n--- Suggestions ---")
        for suggestion in result['suggestions']:
            print(f"  • {suggestion}")

        # Test 2: Specific question
        print("\n" + "=" * 60)
        print("\n2. Running analysis with specific question...")
        question = "What types of trees would be suitable for this location?"

        result2 = await tool.execute(
            image_path=str(path),
            question=question
        )

        print(f"\nQuestion: {question}")
        print("\n--- Analysis ---")
        print(result2['analysis'])

        print("\n" + "=" * 60)
        print("Tests completed successfully!")

    except Exception as e:
        print(f"\nError during analysis: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    asyncio.run(test_photo_analysis(image_path))
