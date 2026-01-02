# bot/handlers/__init__.py
# ===== REFACTORED HANDLERS (v3) =====
# [2025-12-29] Рефакторинг: creation.py разделен на 4 модуля
# [2025-12-29] FIXED: Изменены абсолютные импорты на относительные
# [2026-01-02] NEW: Добавлен edit_design раутер для EDIT_DESIGN режима

from .creation_main import router as router_main
from .creation_new_design import router as router_new_design
from .creation_exterior_interior import router as router_exterior
from .creation_extras import router as router_extras
from .edit_design import router as router_edit_design

__all__ = [
    'router_main',
    'router_new_design',
    'router_exterior',
    'router_extras',
    'router_edit_design',
]
