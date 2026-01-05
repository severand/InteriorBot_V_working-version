"""Test script for Qwen-VL Facade Analyzer

Run: python test_analyzer.py <image_path>
Example: python test_analyzer.py test_facade.jpg
"""

import sys
import logging
from pathlib import Path
from analyzer import get_facade_analyzer

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def test_analyzer(image_path: str) -> None:
    """Test facade analyzer with provided image"""
    
    print("=" * 70)
    print("🚀 QWEN-VL FACADE ANALYZER TEST")
    print("=" * 70)
    
    # 1. Verify image exists
    image_path_obj = Path(image_path)
    if not image_path_obj.exists():
        print(f"❌ Image not found: {image_path}")
        return
    
    print(f"\n📸 Image: {image_path}")
    print(f"   Size: {image_path_obj.stat().st_size / 1024 / 1024:.2f} MB")
    
    # 2. Initialize analyzer
    print(f"\n📥 Initializing Qwen-VL analyzer...")
    try:
        analyzer = get_facade_analyzer()
        print("✅ Analyzer initialized")
    except Exception as e:
        print(f"❌ Failed to initialize: {e}")
        return
    
    # 3. Analyze
    print(f"\n🔄 Analyzing facade (this may take 30-60 seconds)...")
    try:
        analysis = analyzer.analyze(image_path, detailed=True)
        print("✅ Analysis complete")
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 4. Display results
    print("\n" + "=" * 70)
    print("📊 ANALYSIS RESULT:")
    print("=" * 70)
    print(analysis)
    print("=" * 70)
    
    # 5. Character count
    print(f"\n📝 Analysis: {len(analysis)} characters")
    print(f"📈 Ready for KIE.AI integration")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_analyzer.py <image_path>")
        print("Example: python test_analyzer.py test_facade.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_analyzer(image_path)
