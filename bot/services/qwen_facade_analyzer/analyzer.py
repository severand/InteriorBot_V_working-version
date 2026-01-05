"""Qwen-VL Facade Analyzer - Main Module"""

import torch
import logging
from transformers import Qwen2VLForConditionalGeneration, AutoProcessor
from qwen_vl_utils import process_vision_info
from typing import Optional

logger = logging.getLogger(__name__)


class QwenFacadeAnalyzer:
    """Analyzes house facades using Qwen-VL model"""

    _instance: Optional['QwenFacadeAnalyzer'] = None
    _initialized: bool = False

    def __new__(cls):
        """Singleton pattern"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize analyzer"""
        if self._initialized:
            return

        self.model_size = "7b"  # Default model
        self.model = None
        self.processor = None
        self._load_model()
        self._initialized = True

    def _load_model(self) -> None:
        """Load Qwen-VL model and processor"""
        try:
            model_id = f"Qwen/Qwen2-VL-{self.model_size}-Instruct"
            logger.info(f"Loading Qwen-VL model: {model_id}")
            logger.info(f"Device: {'CUDA' if torch.cuda.is_available() else 'CPU'}")

            self.model = Qwen2VLForConditionalGeneration.from_pretrained(
                model_id,
                torch_dtype="auto",
                device_map="auto"
            )

            self.processor = AutoProcessor.from_pretrained(model_id)

            logger.info("✅ Qwen-VL model loaded successfully")

        except Exception as e:
            logger.error(f"❌ Failed to load Qwen-VL: {e}")
            raise

    def analyze(self, image_path: str, detailed: bool = True) -> str:
        """Analyze facade and return description

        Args:
            image_path: Path to facade image
            detailed: If True, return detailed analysis

        Returns:
            Facade description for AI generation
        """
        if not self.model or not self.processor:
            raise RuntimeError("Model not loaded. Call __init__ first.")

        # Prepare prompt
        if detailed:
            prompt = """Analyze this house facade in architectural detail:
1. Architectural style (modern, classic, colonial, contemporary, etc)
2. Materials used (brick, wood, siding, stone, stucco, cladding, etc)
3. Color palette (specific colors of walls, roof, trim, accents)
4. Window type, style, and arrangement
5. Door design and materials
6. Roof type and material
7. Decorative elements and details
8. Overall design characteristics
9. Any distinctive features

Create a detailed description suitable for AI image generation."""
        else:
            prompt = """Analyze this house facade:
1. Architectural style
2. Materials
3. Colors
4. Windows and doors
5. Roof type

Be concise."""

        messages = [{
            "role": "user",
            "content": [
                {"type": "image", "image": image_path},
                {"type": "text", "text": prompt}
            ]
        }]

        # Process inputs
        logger.debug("Processing inputs...")
        text = self.processor.apply_chat_template(
            messages,
            tokenize=False,
            add_generation_prompt=True
        )

        image_inputs, video_inputs = process_vision_info(messages)

        inputs = self.processor(
            text=[text],
            images=image_inputs,
            videos=video_inputs,
            padding=True,
            return_tensors="pt",
        )

        device = "cuda" if torch.cuda.is_available() else "cpu"
        inputs = inputs.to(device)

        # Generate
        logger.debug("Generating analysis...")
        with torch.no_grad():
            generated_ids = self.model.generate(
                **inputs,
                max_new_tokens=500,
                temperature=0.7,
                top_p=0.9,
            )

        # Decode
        generated_ids_trimmed = [
            out_ids[len(in_ids):]
            for in_ids, out_ids in zip(inputs.input_ids, generated_ids)
        ]

        output_text = self.processor.batch_decode(
            generated_ids_trimmed,
            skip_special_tokens=True,
            clean_up_tokenization_spaces=False
        )[0]

        logger.info(f"Analysis complete: {len(output_text)} characters")
        return output_text


# Singleton instance
_analyzer_instance: Optional[QwenFacadeAnalyzer] = None


def get_facade_analyzer() -> QwenFacadeAnalyzer:
    """Get or create facade analyzer instance

    Returns:
        QwenFacadeAnalyzer instance
    """
    global _analyzer_instance
    if _analyzer_instance is None:
        _analyzer_instance = QwenFacadeAnalyzer()
    return _analyzer_instance
