# 🚀 НА АКТИВАЦИИ NANO BANANA (KIE.AI API)

**Статус:** ✅ ОТОП К АКТИВАЦИИ

**Дата актуализации:** 2025-12-23 08:37

---

## ✍️ МИНУтовая АКТИВАЦИЯ (3 урока)

### ШАГ 1: Обновите .env (2 мин)

Найдите .env в репои:  
```bash
cat > .env << 'EOF'
# ... все текущие строки ...

# ===== NANO BANANA (KIE.AI) =====
KIE_API_KEY=sk_kie_YOUR_KEY_HERE  # Получите на https://kie.ai/account
USE_KIE_API=True                  # ЭТО ВКЛЮЧАЕТ NANO BANANA!
KIE_NANO_BANANA_FORMAT=png
KIE_NANO_BANANA_SIZE=auto
EOF
```

**Как получить KIE_API_KEY:**
1. Откройте https://kie.ai/account
2. Нажмите **API Keys**
3. скопируйте ключ
4. Пасть в .env

### ШАГ 2: Проверьте конфиг (1 мин)

```bash
cd bot
python -c "from config_kie import config_kie; print(config_kie.info())"

# Оно:
# ✅ KIE.AI NANO BANANA API КОНФИГ:
#   API KEY installed: True
#   USE_KIE_API: True
#   Format: png
#   Size: auto
```

### ШАГ 3: ТЕСТИРОВАНИЕ (30 сек)

```bash
# Проверьте API
python test_kie_api.py

# Ожидаемые результаты:
# Test 1: API Key Configuration ... ✅
# Test 2: Module Imports ... ✅
# Test 3: Config Validation ... ✅
# Test 4: API Connectivity ... ✅
# Success Rate: 100%
```

Окей! Активируя проверен.

---

## 📄 ПЕРЕКЛЮЧЕНИЕ МЕЖДУ API

### ВКЛЮЧИТЬ Nano Banana (Kie.ai):
```env
USE_KIE_API=True
```

### ВЕРНУТЬСЯ НА Replicate:
```env
USE_KIE_API=False
```

### ПЕрезагружите бот:
```bash
sudo systemctl restart interior-bot
# или
./restart_bot.sh
```

---

## 📂 ПРОВЕРКА В ТЕЛЕГРАМЕ

1. `/start` в боте
2. Кнопка **🎨 Создать дизайн**
3. Нагружите фото
4. Выберите настройки (room, style)
5. **Очеките до 10 сек для результата**

Нано Banana быстрые, экономные результаты! 🚀

---

## ☢️ ПОГРУЖКА: Ошибки

### "Ошибка: KIE_API_KEY not found"
```bash
# Проверьте:
grep "KIE_API_KEY" .env
echo "$KIE_API_KEY"
```

### "Нет ответа от API"
```bash
# Проверьте интернет:
ping -c 1 google.com

# Проверьте статус:
https://kie.ai/status

# Пробуете curl:
curl -X POST https://api.kie.ai/generate \
  -H "Authorization: Bearer $KIE_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model": "google/nano-banana", "input": {"prompt": "test"}}'
```

### "Insufficient credits"
Перейдите на https://kie.ai/account и наполните баланс.

---

## 🚀 ГОТОВО!

**✅ ТОЛЬКО NANO BANANA деплоймент. Бес лишних моделей.**
