"""Example integration of Qwen-VL with KIE.AI for facade transformation

This example shows how to:
1. Load facade photo from Telegram
2. Analyze with Qwen-VL
3. Generate prompt for KIE.AI
4. Transform facade
5. Send result back to user
"""

import logging
from pathlib import Path
from typing import Optional

from analyzer import get_facade_analyzer
from utils import prepare_prompt, format_analysis_for_display, validate_analysis

logger = logging.getLogger(__name__)


class FacadeTransformationPipeline:
    """Full pipeline for facade analysis and transformation"""
    
    def __init__(self, kie_ai_client=None):
        """Initialize pipeline
        
        Args:
            kie_ai_client: KIE.AI client instance (optional)
        """
        self.analyzer = get_facade_analyzer()
        self.kie_ai_client = kie_ai_client
    
    async def transform_facade(
        self,
        original_facade_path: str,
        reference_style: Optional[str] = None,
        reference_image_path: Optional[str] = None
    ) -> dict:
        """Full transformation pipeline
        
        Args:
            original_facade_path: Path to original facade image
            reference_style: Description of reference style
            reference_image_path: Path to reference style image (optional)
            
        Returns:
            Dictionary with:
            - analysis: Qwen-VL facade analysis
            - prompt: Enhanced prompt for KIE.AI
            - result_image_url: URL to transformed facade (if KIE.AI integrated)
        """
        
        logger.info(f"Starting facade transformation pipeline...")
        
        # Step 1: Analyze original facade
        logger.info(f"Step 1: Analyzing original facade...")
        analysis = self.analyzer.analyze(
            original_facade_path,
            detailed=True
        )
        
        if not validate_analysis(analysis):
            raise ValueError("Invalid facade analysis")
        
        logger.info(f"Analysis complete: {len(analysis)} characters")
        
        # Step 2: Prepare enhanced prompt
        logger.info(f"Step 2: Preparing enhanced prompt...")
        enhanced_prompt = prepare_prompt(
            facade_analysis=analysis,
            reference_style=reference_style
        )
        
        logger.info(f"Prompt ready: {len(enhanced_prompt)} characters")
        
        # Step 3: Generate with KIE.AI (if client available)
        result_url = None
        if self.kie_ai_client:
            logger.info(f"Step 3: Generating with KIE.AI...")
            try:
                result_url = await self.kie_ai_client.generate(
                    original_image=original_facade_path,
                    reference_image=reference_image_path,
                    prompt=enhanced_prompt
                )
                logger.info(f"Generation complete: {result_url}")
            except Exception as e:
                logger.error(f"KIE.AI generation failed: {e}")
                # Don't fail pipeline, just skip this step
        
        return {
            "analysis": analysis,
            "prompt": enhanced_prompt,
            "result_image_url": result_url,
            "status": "success"
        }
    
    async def batch_analyze(
        self,
        image_paths: list
    ) -> list:
        """Analyze multiple facades
        
        Args:
            image_paths: List of facade image paths
            
        Returns:
            List of analysis results
        """
        results = []
        
        for i, image_path in enumerate(image_paths, 1):
            logger.info(f"Analyzing {i}/{len(image_paths)}: {image_path}")
            try:
                analysis = self.analyzer.analyze(image_path, detailed=True)
                results.append({
                    "image": image_path,
                    "analysis": analysis,
                    "status": "success"
                })
            except Exception as e:
                logger.error(f"Failed to analyze {image_path}: {e}")
                results.append({
                    "image": image_path,
                    "error": str(e),
                    "status": "failed"
                })
        
        return results


# ============================================================================
# TELEGRAM BOT HANDLER EXAMPLE
# ============================================================================

class FacadeTransformationHandler:
    """Handler for Telegram bot facade transformation commands"""
    
    def __init__(self, bot, kie_ai_client=None):
        """Initialize handler
        
        Args:
            bot: Telegram bot instance
            kie_ai_client: KIE.AI client
        """
        self.bot = bot
        self.pipeline = FacadeTransformationPipeline(kie_ai_client)
        self.user_sessions = {}  # Store user's facade data
    
    async def handle_facade_photo(
        self,
        user_id: int,
        photo_file_path: str
    ) -> None:
        """Handle facade photo upload
        
        Args:
            user_id: Telegram user ID
            photo_file_path: Path to downloaded photo
        """
        logger.info(f"User {user_id} uploaded facade photo")
        
        try:
            # Show loading message
            loading_msg = await self.bot.send_message(
                user_id,
                "🔄 Analyzing your facade... This may take 30-60 seconds..."
            )
            
            # Analyze
            analysis = self.pipeline.analyzer.analyze(
                photo_file_path,
                detailed=True
            )
            
            # Validate
            if not validate_analysis(analysis):
                await self.bot.edit_message_text(
                    "❌ Analysis failed. Please upload a clearer photo of your house facade.",
                    user_id,
                    loading_msg.message_id
                )
                return
            
            # Store in session
            self.user_sessions[user_id] = {
                "facade_path": photo_file_path,
                "analysis": analysis
            }
            
            # Format and display analysis
            display_text = format_analysis_for_display(analysis, max_length=500)
            
            await self.bot.edit_message_text(
                f"🏠 **Facade Analysis:**\n\n{display_text}\n\n"
                f"Now, send me a reference style photo (or describe the style you want).",
                user_id,
                loading_msg.message_id
            )
            
        except Exception as e:
            logger.error(f"Error analyzing facade: {e}")
            await self.bot.send_message(
                user_id,
                f"❌ Error: {str(e)}"
            )
    
    async def handle_reference_style(
        self,
        user_id: int,
        reference_image_path: str = None,
        style_description: str = None
    ) -> None:
        """Handle reference style photo or description
        
        Args:
            user_id: Telegram user ID
            reference_image_path: Path to reference image (optional)
            style_description: Text description of style (optional)
        """
        logger.info(f"User {user_id} provided reference style")
        
        if user_id not in self.user_sessions:
            await self.bot.send_message(
                user_id,
                "Please upload your facade photo first."
            )
            return
        
        try:
            session = self.user_sessions[user_id]
            
            # Show generating message
            generating_msg = await self.bot.send_message(
                user_id,
                "⏳ Transforming your facade... This may take 1-2 minutes..."
            )
            
            # Run transformation
            result = await self.pipeline.transform_facade(
                original_facade_path=session["facade_path"],
                reference_style=style_description,
                reference_image_path=reference_image_path
            )
            
            if result["result_image_url"]:
                # Send transformed facade
                await self.bot.send_photo(
                    user_id,
                    result["result_image_url"],
                    caption="🏠 Your transformed facade!"
                )
            else:
                # Send prompt for manual transformation
                await self.bot.send_message(
                    user_id,
                    f"Transformation prompt ready:\n\n{result['prompt']}"
                )
            
            # Cleanup
            del self.user_sessions[user_id]
            
        except Exception as e:
            logger.error(f"Error transforming facade: {e}")
            await self.bot.send_message(
                user_id,
                f"❌ Transformation failed: {str(e)}"
            )


# ============================================================================
# USAGE EXAMPLE
# ============================================================================

if __name__ == "__main__":
    """
    Example usage:
    
    # Simple analysis
    pipeline = FacadeTransformationPipeline()
    result = await pipeline.transform_facade(
        "original_facade.jpg",
        reference_style="Modern minimalist"
    )
    print(result["analysis"])
    print(result["prompt"])
    
    # With KIE.AI (async)
    pipeline = FacadeTransformationPipeline(kie_ai_client=your_kie_client)
    result = await pipeline.transform_facade(
        "original_facade.jpg",
        reference_style="Scandinavian",
        reference_image_path="reference.jpg"
    )
    print(f"Transformed: {result['result_image_url']}")
    
    # In Telegram bot
    handler = FacadeTransformationHandler(bot, kie_ai_client)
    await handler.handle_facade_photo(user_id=123456, photo_file_path="facade.jpg")
    """
    pass
