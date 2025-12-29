# bot/handlers/__init__.py
# ===== REFACTORED HANDLERS (v3) =====
# [2025-12-29] Рефакторинг: creation.py разделен на 4 модуля

from bot.handlers.creation_main import router as router_main
from bot.handlers.creation_new_design import router as router_new_design
from bot.handlers.creation_exterior_interior import router as router_exterior
from bot.handlers.creation_extras import router as router_extras

__all__ = [
    'router_main',
    'router_new_design',
    'router_exterior',
    'router_extras',
]
