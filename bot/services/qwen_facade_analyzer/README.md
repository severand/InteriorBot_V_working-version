# 🏗️ Qwen-VL Facade Analyzer

Integrate Qwen-VL model for intelligent house facade analysis in your InteriorBot project.

## 📋 Overview

This module provides:
- **Qwen-VL Integration**: Analyze house facades using state-of-the-art vision language model
- **Architectural Analysis**: Identify style, materials, colors, windows, doors, and decorative elements
- **Prompt Enhancement**: Generate detailed prompts for KIE.AI facade transformation
- **Singleton Pattern**: Efficient model loading and memory management

## 🚀 Quick Start

### 1. Installation

```bash
# Install dependencies
pip install -r services/qwen_facade_analyzer/requirements.txt
```

### 2. Test the Analyzer

```bash
# Run test script
cd bot/services/qwen_facade_analyzer
python test_analyzer.py /path/to/facade.jpg
```

### 3. Integrate into Your Bot

```python
from services.qwen_facade_analyzer import get_facade_analyzer

# Get analyzer instance (loads model on first call)
analyzer = get_facade_analyzer()

# Analyze a facade
analysis = analyzer.analyze("path/to/facade.jpg", detailed=True)
print(analysis)
```

## 📚 API Reference

### QwenFacadeAnalyzer

```python
class QwenFacadeAnalyzer:
    def __init__(self, model_size: str = "7b"):
        """Initialize analyzer
        
        Args:
            model_size: "7b" (default) or "2b" (smaller model)
        """
    
    def analyze(self, image_path: str, detailed: bool = True) -> str:
        """Analyze facade and return description
        
        Args:
            image_path: Path to facade image
            detailed: If True, return detailed analysis
            
        Returns:
            Facade description for AI generation
        """
```

### Utility Functions

```python
from services.qwen_facade_analyzer.utils import (
    prepare_prompt,
    extract_style_description,
    format_analysis_for_display,
    validate_analysis
)

# Prepare enhanced prompt for KIE.AI
prompt = prepare_prompt(
    facade_analysis=analysis,
    reference_style="Modern minimalist"
)

# Extract specific style elements
styles = extract_style_description(analysis)
print(styles['materials'])  # Extract materials
print(styles['colors'])     # Extract colors

# Format for Telegram display
display_text = format_analysis_for_display(analysis, max_length=500)

# Validate analysis quality
if validate_analysis(analysis):
    print("Analysis is valid")
```

## 🔧 Configuration

### Model Sizes

- **7B (default)**: Better quality, requires 8GB+ VRAM
- **2B**: Faster, requires 4GB+ VRAM

```python
# Use smaller model
analyzer = get_facade_analyzer(model_size="2b")
```

### Device Detection

Automatically uses CUDA if available, falls back to CPU.

```python
import torch
device = "cuda" if torch.cuda.is_available() else "cpu"
print(f"Using: {device}")
```

## 📊 Example Usage

### Basic Analysis

```python
from services.qwen_facade_analyzer import get_facade_analyzer

analyzer = get_facade_analyzer()
analysis = analyzer.analyze("my_house.jpg")
print(analysis)
```

### With Enhanced Prompt

```python
from services.qwen_facade_analyzer import get_facade_analyzer
from services.qwen_facade_analyzer.utils import prepare_prompt

analyzer = get_facade_analyzer()
analysis = analyzer.analyze("my_house.jpg")

# Prepare prompt for KIE.AI
enhanced_prompt = prepare_prompt(
    facade_analysis=analysis,
    reference_style="Scandinavian modern"
)

print(enhanced_prompt)
```

### Integration with Bot Handler

```python
from services.qwen_facade_analyzer import get_facade_analyzer
from services.qwen_facade_analyzer.utils import format_analysis_for_display

async def handle_facade_photo(user_id, photo_path):
    """Handle facade photo from user"""
    
    # Analyze facade
    analyzer = get_facade_analyzer()
    analysis = analyzer.analyze(photo_path)
    
    # Format for display
    display_text = format_analysis_for_display(analysis)
    
    # Send to user
    await bot.send_message(
        user_id,
        f"🏠 Facade Analysis:\n\n{display_text}"
    )
    
    # Store for later use
    user_data[user_id]['facade_analysis'] = analysis
```

## ⚠️ Requirements

### Hardware
- **GPU Memory**: 8GB (7B model) or 4GB (2B model)
- **System RAM**: 16GB+ recommended
- **Storage**: ~15GB for model download

### Software
- Python 3.8+
- PyTorch 2.0+
- CUDA 11.8+ (optional, for GPU acceleration)

## 🐛 Troubleshooting

### Out of Memory Error

```python
# Use smaller model
analyzer = get_facade_analyzer(model_size="2b")

# Or enable 8-bit quantization (requires bitsandbytes)
model = Qwen2VLForConditionalGeneration.from_pretrained(
    "Qwen/Qwen2-VL-7B-Instruct",
    load_in_8bit=True,
    device_map="auto"
)
```

### Slow Inference

```python
# Install acceleration packages
pip install accelerate

# Use optimized settings
generator_kwargs = dict(
    max_new_tokens=300,
    temperature=0.7,
    do_sample=True
)
```

### CUDA Not Available

```bash
# Install CUDA-enabled PyTorch
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

## 📖 Documentation

- [Qwen-VL GitHub](https://github.com/QwenLM/Qwen-VL)
- [HuggingFace Model Card](https://huggingface.co/Qwen/Qwen2-VL-7B-Instruct)
- [Transformers Documentation](https://huggingface.co/docs/transformers/)

## 📝 Development

### Run Tests

```bash
cd bot/services/qwen_facade_analyzer
python test_analyzer.py test_facade.jpg
```

### Add Custom Analysis

Extend `QwenFacadeAnalyzer` class:

```python
from services.qwen_facade_analyzer import QwenFacadeAnalyzer

class CustomFacadeAnalyzer(QwenFacadeAnalyzer):
    def analyze_with_context(self, image_path, context):
        # Custom analysis logic
        pass
```

## 🤝 Contributing

Contributions welcome! Please:
1. Test thoroughly
2. Document changes
3. Submit PR to `develop` branch

## 📄 License

Same as parent project

## 🎯 Roadmap

- [ ] Fine-tuning for Russian architecture
- [ ] Batch processing support
- [ ] Caching for repeated analyses
- [ ] Multi-language support
- [ ] Integration with more image generation models

---

**Branch**: `feature/qwen-vl-facade-analyzer`  
**Status**: ✅ Ready for testing
