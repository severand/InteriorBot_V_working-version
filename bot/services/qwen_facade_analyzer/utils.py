"""Utility functions for Qwen-VL Facade Analysis"""

import re
from typing import Dict, List, Optional


def prepare_prompt(
    facade_analysis: str,
    reference_style: Optional[str] = None,
    original_prompt: Optional[str] = None
) -> str:
    """Prepare enhanced prompt for KIE.AI facade transformation
    
    Args:
        facade_analysis: Qwen-VL analysis of original facade
        reference_style: Optional description of reference style
        original_prompt: Optional original prompt from V0
        
    Returns:
        Enhanced prompt for KIE.AI
    """
    
    base_prompt = original_prompt or """Transform the house facade to match the reference design.

CRITICAL (DO NOT BREAK - 100% PRIORITY):
- Keep exact house shape and structure
- Keep exact roof shape and angle
- Keep exact window positions and sizes
- Keep exact door positions and sizes
- Keep exact building height, width, proportions
- Do NOT add or remove any parts of the house

OPTIONAL (Can do if possible):
- Apply colors from reference
- Apply materials from reference
- Apply decorative style from reference

Create photorealistic result."""
    
    enhanced = f"""{base_prompt}

--- ORIGINAL FACADE ANALYSIS ---
{facade_analysis}"""
    
    if reference_style:
        enhanced += f"""

--- REFERENCE STYLE ---
{reference_style}"""
    
    return enhanced


def extract_style_description(facade_analysis: str) -> Dict[str, str]:
    """Extract key style elements from facade analysis
    
    Args:
        facade_analysis: Full Qwen-VL analysis
        
    Returns:
        Dictionary with extracted style elements
    """
    
    result = {
        "style": "",
        "materials": "",
        "colors": "",
        "windows": "",
        "doors": "",
        "roof": "",
        "decorative": ""
    }
    
    lines = facade_analysis.split('\n')
    current_key = None
    
    for line in lines:
        line_lower = line.lower()
        
        # Detect style
        if any(x in line_lower for x in ['style', 'architectural']):
            current_key = 'style'
        # Detect materials
        elif any(x in line_lower for x in ['material', 'brick', 'wood', 'siding', 'stone', 'stucco']):
            current_key = 'materials'
        # Detect colors
        elif any(x in line_lower for x in ['color', 'palette', 'tone', 'shade']):
            current_key = 'colors'
        # Detect windows
        elif any(x in line_lower for x in ['window', 'glazing', 'pane']):
            current_key = 'windows'
        # Detect doors
        elif any(x in line_lower for x in ['door', 'entrance', 'entry']):
            current_key = 'doors'
        # Detect roof
        elif any(x in line_lower for x in ['roof', 'roofing', 'shingle', 'tile']):
            current_key = 'roof'
        # Detect decorative
        elif any(x in line_lower for x in ['decorative', 'ornament', 'detail', 'trim', 'accent']):
            current_key = 'decorative'
        
        if current_key and line.strip():
            result[current_key] += line.strip() + " "
    
    # Clean up
    for key in result:
        result[key] = result[key].strip()
    
    return result


def format_analysis_for_display(analysis: str, max_length: int = 500) -> str:
    """Format analysis for Telegram display
    
    Args:
        analysis: Full analysis text
        max_length: Maximum characters to display
        
    Returns:
        Formatted text for display
    """
    
    if len(analysis) <= max_length:
        return analysis
    
    # Truncate to max_length
    truncated = analysis[:max_length]
    
    # Try to cut at sentence boundary
    last_period = truncated.rfind('.')
    if last_period > max_length * 0.8:
        truncated = truncated[:last_period + 1]
    
    return truncated + "..." if len(analysis) > len(truncated) else truncated


def validate_analysis(analysis: str) -> bool:
    """Validate that analysis is reasonable
    
    Args:
        analysis: Facade analysis text
        
    Returns:
        True if analysis seems valid
    """
    
    if not analysis or len(analysis) < 50:
        return False
    
    if len(analysis) > 5000:
        return False
    
    # Check for common architecture terms
    lower = analysis.lower()
    architecture_terms = [
        'house', 'facade', 'building', 'style', 'window', 'door',
        'material', 'color', 'roof', 'wall', 'brick', 'wood',
        'modern', 'classic', 'contemporary', 'design'
    ]
    
    found_terms = sum(1 for term in architecture_terms if term in lower)
    
    return found_terms >= 3
