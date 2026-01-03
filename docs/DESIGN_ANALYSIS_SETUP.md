# 🚀 DESIGN ANALYSIS - SETUP & IMPLEMENTATION GUIDE

## 📁 Оглавление

1. [Quick Start](#quick-start)
2. [Шаг-шаг имплементация](#шаг-шаг-имплементация)
3. [Структура папок](#структура-папок)
4. [Коды](#коды)
5. [Настройка](#настройка)
6. [Ошибки и FAQ](#ошибки-и-faq)

---

## ⚡ QUICK START

### 1. Основные понятия

**Основные ресурсы:**
```
📄 docs/DESIGN_ANALYSIS_PROJECT.md    <- Основная документация
📖 docs/DESIGN_ANALYSIS_API.md        <- API референция
🚀 docs/DESIGN_ANALYSIS_SETUP.md      <- Этот файл
```

### 2. Все дно на установку

```bash
# Клонирование репо
ситория и основные папки
git clone https://github.com/severand/InteriorBot_V_working-version.git
cd InteriorBot_V_working-version

# Основные зависимости
pip install openai anthropic google-generativeai python-dotenv

# Настройка .env
cp .env.example .env
# и добавь один из ключей:
# OPENAI_API_KEY=sk-proj-xxxxx
# или ANTHROPIC_API_KEY=sk-ant-xxxxx
# или GOOGLE_API_KEY=AIzaxxxxx

# Начинаем имплементацию
# Смотри "ШАГ-ШАГ ИМПЛЕМЕНТАЦИЙ" ниже
```

---

## 🔧 ШАГ-ШАГ ИМПЛЕМЕНТАЦИЯ

### ШАГ 1: Создание файла `bot/services/vision_analysis.py`

Копируй код из ниже и сохрани в этот файл:

**[TODO: Полный код в применах коды ниже]**

### ШАГ 2: Создание файла `bot/services/design_parser.py`

**[TODO: Полный код в применах коды ниже]**

### ШАГ 3: Создание файла `bot/services/design_cache.py`

**[TODO: Полный код в применах коды ниже]**

### ШАГ 4: Создание файла `bot/handlers/design_analysis.py`

**[TODO: Полный код в применах коды ниже]**

### ШАГ 5: Обновление `bot/handlers/creation_sample_design.py`

Найди в файле функцию `generate_try_on_handler` и добавь основное действие:

```python
# В энде данного handler (после отправки SCREEN 12 меню):

# Сохрания URL для анализа
await state.update_data(
    last_generated_image_url=result_url
)
```

### ШАГ 6: Обновление `bot/keyboards/inline.py`

Найди функцию `get_post_generation_sample_keyboard()` и добавь кнопку:

```python
def get_post_generation_sample_keyboard():
    keyboard = InlineKeyboardBuilder()
    
    # НОВАЯ КНОПКА:
    keyboard.button(
        text="📋 Описание дизайна",
        callback_data="get_design_description"
    )
    
    # старые кнопки:
    keyboard.button(
        text="🔄 Новый образец",
        callback_data="new_sample"
    )
    keyboard.button(
        text="🏠 Главное меню",
        callback_data="main_menu"
    )
    
    keyboard.adjust(1)  # каждая кнопка на новой строке
    return keyboard.as_markup()
```

### ШАГ 7: Настройка .env

Открой `.env` и добавь один из:

```env
# ОПЦИОН А: GPT-4 Vision (ЛУЧШОЕ КАЧЕСТВО)
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxxx
VISION_PROVIDER=gpt

# ОПЦИОН Б: Claude Vision
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxx
VISION_PROVIDER=claude

# ОПЦИОН В: Google Gemini (БЕСПЛАТНО)
GOOGLE_API_KEY=AIzaxxxxxxxxxxxxxxxxxxxxx
VISION_PROVIDER=gemini
```

### ШАГ 8: Миграция БД

Создай файл `bot/database/migrations/001_design_analysis.sql`:

```sql
CREATE TABLE IF NOT EXISTS design_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    image_url TEXT NOT NULL,
    image_hash TEXT UNIQUE NOT NULL,
    style TEXT,
    walls_color TEXT,
    walls_ral TEXT,
    walls_material TEXT,
    floor_material TEXT,
    floor_color TEXT,
    ceiling_type TEXT,
    full_json TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(user_id)
);

-- Индексы
CREATE INDEX idx_design_analysis_user_id ON design_analysis(user_id);
CREATE INDEX idx_design_analysis_hash ON design_analysis(image_hash);
```

запусти миграцию:
```bash
sqlite3 bot/database/bot.db < bot/database/migrations/001_design_analysis.sql
```

### ШАГ 9: Новые методы БД

в `bot/database/db.py` добавь методы:

```python
class Database:
    
    async def save_design_analysis(self, user_id: int, image_hash: str, analysis: dict) -> bool:
        """
        Сохраняет анализ дизайна в БД
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(
                    """
                    INSERT OR REPLACE INTO design_analysis
                    (user_id, image_hash, style, walls_color, walls_ral, 
                     walls_material, floor_material, floor_color, 
                     ceiling_type, full_json, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        user_id,
                        image_hash,
                        analysis.get('style'),
                        analysis.get('walls', {}).get('color'),
                        analysis.get('walls', {}).get('ral_code'),
                        analysis.get('walls', {}).get('material'),
                        analysis.get('floor', {}).get('material'),
                        analysis.get('floor', {}).get('color'),
                        analysis.get('ceiling', {}).get('type'),
                        json.dumps(analysis)
                    )
                )
                await db.commit()
            return True
        except Exception as e:
            logger.error(f"Ошибка сохранения анализа: {e}")
            return False
    
    async def get_design_analysis(self, image_hash: str) -> dict | None:
        """
        Получает сохраненный анализ
        """
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                async with db.execute(
                    "SELECT full_json FROM design_analysis WHERE image_hash = ?",
                    (image_hash,)
                ) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return json.loads(row['full_json'])
            return None
        except Exception as e:
            logger.error(f"Ошибка получения анализа: {e}")
            return None
```

---

## 📁 СТРУКТУРА ПАПОК

```
bot/
├── services/
│   ├── vision_analysis.py      ✅ НОВЫЙ
│   ├── design_parser.py        ✅ НОВЫЙ
│   └── design_cache.py         ✅ НОВЫЙ
│
├── handlers/
│   ├── design_analysis.py      ✅ НОВЫЙ
│   └── creation_sample_design.py 📍 ОБНОВЛЕН
│
├── keyboards/
│   └── inline.py                📍 ОБНОВЛЕН
│
├── database/
│   ├── db.py                    📍 ОБНОВЛЕН
│   └── migrations/
│       └── 001_design_analysis.sql  ✅ НОВЫЙ
│
├── config/
│   └── .env                     📍 ОБНОВЛЕН
│
├── main.py                  📍 ОБНОВЛЕН
│   # Нужно включить роутер:
│   # from handlers.design_analysis import router as design_router
│   # ...
│   # dp.include_router(design_router)
│
└── logs/
    └── design_analysis.log      ✅ Кэринг
```

---

## 💾 КОДЫ

### `vision_analysis.py`

**[ПОЛНЫЙ КОД - смотри примеры ниже в разделе ПРИМЕРЫ]**

**Краткий обзор:**
```python
from enum import Enum
from typing import Optional, Dict
import openai
import anthropic
import google.generativeai as genai
from config import config

class VisionProvider(str, Enum):
    GPT = "gpt"
    CLAUDE = "claude"
    GEMINI = "gemini"

class DesignAnalyzer:
    def __init__(self, provider: str = None):
        self.provider = provider or config.VISION_PROVIDER
        
    async def analyze(self, image_url: str) -> dict:
        if self.provider == VisionProvider.GPT:
            return await self._analyze_with_gpt(image_url)
        elif self.provider == VisionProvider.CLAUDE:
            return await self._analyze_with_claude(image_url)
        elif self.provider == VisionProvider.GEMINI:
            return await self._analyze_with_gemini(image_url)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    async def _analyze_with_gpt(self, image_url: str) -> dict:
        # ... реализация ...
        pass
    
    async def _analyze_with_claude(self, image_url: str) -> dict:
        # ... реализация ...
        pass
    
    async def _analyze_with_gemini(self, image_url: str) -> dict:
        # ... реализация ...
        pass
```

---

## ⚙️ НАСТРОЙКА

### Переменные окружения

```env
# Выбор провайдера
VISION_PROVIDER=gpt  # gpt, claude, gemini

# API ключи
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
GOOGLE_API_KEY=

# Логирование
DESIGN_ANALYSIS_LOG_LEVEL=INFO
DESIGN_ANALYSIS_LOG_FILE=bot/logs/design_analysis.log

# Кэширование
DESIGN_ANALYSIS_CACHE_TTL=86400  # 24 часа
DESIGN_ANALYSIS_CACHE_REDIS=false  # true если используешь Redis
```

### Импорты в `main.py`

```python
# bot/main.py

from handlers.design_analysis import router as design_router

# ...

async def main():
    # ...
    dp.include_router(design_router)
    # ...
```

### Инициализация БД

```bash
# Один раз при первом запуске
sqlite3 bot/database/bot.db < bot/database/migrations/001_design_analysis.sql
```

---

## ⚠️ ОШИБКИ И FAQ

### Ошибка: "API key not found"

**Решение:**
1. Убедись что .env содержит нужный ключ
2. Проверь VISION_PROVIDER значение
3. Перезагрузи бот

### Ошибка: "Invalid image URL"

**Решение:**
1. Убедись что URL доступен
2. Используй прямую ссылку на изображение
3. Проверь формат (JPG, PNG)

### Ошибка: "Parse error"

**Решение:**
1. API вернул неверный JSON
2. Попробуй другого провайдера
3. Проверь логи: `bot/logs/design_analysis.log`

### Ошибка: "Database error"

**Решение:**
1. Проверь что миграция выполнена
2. Убедись в правах на файл БД
3. Перезагрузи приложение

### FAQ

**В: Какой провайдер лучше?**
О: GPT-4 Vision - лучшее качество, но платный. Gemini - бесплатный, достаточно хороший.

**В: Сколько стоит?**
О: GPT: $0.03/запрос, Claude: $0.015/запрос, Gemini: бесплатно.

**В: Как переключиться между провайдерами?**
О: Измени VISION_PROVIDER в .env

**В: Почему медленно работает?**
О: Vision API требует время. Используй кэширование (design_cache.py)

**В: Как добавить Redis для кэша?**
О: Установи Redis, затем используй design_cache с Redis backend.

---

## ✅ CHECKLIST ФИНАЛЬНОЙ ПРОВЕРКИ

- [ ] Все файлы созданы (3 сервиса + 1 handler)
- [ ] .env обновлен с API ключом
- [ ] Миграция БД выполнена
- [ ] keyboard обновлена с новой кнопкой
- [ ] Методы БД добавлены
- [ ] Импорты в main.py добавлены
- [ ] Логирование настроено
- [ ] Тестирование пройдено (см. выше FAQ)
- [ ] Код в гите (git add + commit + push)
- [ ] Все работает на production

---

## 📁 ПОЛЕЗНЫЕ ССЫЛКИ

- [API Reference](DESIGN_ANALYSIS_API.md)
- [Project Overview](DESIGN_ANALYSIS_PROJECT.md)
- [OpenAI API Docs](https://platform.openai.com/docs/vision)
- [Claude Vision Docs](https://docs.anthropic.com/vision)
- [Google Gemini Docs](https://ai.google.dev/tutorials/vision)

---

**Готово к запуску! 🚀**

