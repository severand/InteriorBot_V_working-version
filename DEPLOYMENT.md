# 🚀 DEPLOYMENT - Продакшн-развёртывание InteriorBot

**Назначение:** Пошаговый гайд по развёртыванию бота в production-среду.  
**Цель:** Минимум ручных действий, максимум предсказуемости.  
**Последнее обновление:** December 12, 2025  

---

## 📋 Содержание

1. [Deployment Strategy](#deployment-strategy)
2. [Production Requirements](#production-requirements)
3. [Single-Server Deployment (VPS)](#single-server-deployment-vps)
4. [Docker-Based Deployment](#docker-based-deployment)
5. [Environment Configuration](#environment-configuration)
6. [Logging & Monitoring](#logging--monitoring)
7. [Backup & Recovery](#backup--recovery)
8. [Security Checklist](#security-checklist)
9. [Deployment Checklist](#deployment-checklist)

---

## 🎯 Deployment Strategy

### Подход по умолчанию

- **1 бот = 1 process** на одном VPS или Docker-контейнере
- **Pooling** (long polling) для Telegram (webhook можно добавить позже)
- **SQLite** как БД (лёгкая нагрузка, нет тяжёлых join'ов)
- **Systemd** или Docker для автозапуска

### Варианты

1. **VPS (Ubuntu/Debian)** — простой контролируемый вариант.
2. **Docker** — изолированное окружение, легко переносить.
3. **PaaS/Cloud** (Heroku, Railway, etc.) — при необходимости, но не базовый сценарий.

---

## 🧱 Production Requirements

### Hardware / OS

```bash
# Минимум
- VPS: 1 vCPU, 1GB RAM, 10GB SSD
- OS: Ubuntu 20.04+ / Debian 11+

# Рекомендуется
- 2 vCPU, 2GB RAM
- Авто-бэкапы диска
```

### Software

```bash
# Требуется
- Python 3.10+
- pip
- git
- systemd (обычно есть в Ubuntu/Debian)

# Опционально
- Docker + docker-compose
- Fail2Ban (от брутфорса)
- Nginx (если нужен HTTPS-прокси)
```

---

## 🖥 Single-Server Deployment (VPS)

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python и pip
sudo apt install -y python3 python3-pip python3-venv git

# Проверка версий
python3 --version    # 3.10+
pip3 --version
```

### Шаг 2: Клонирование проекта

```bash
cd /opt
sudo git clone https://github.com/severand/InteriorBot.git
sudo chown -R $USER:$USER InteriorBot
cd InteriorBot
```

### Шаг 3: Виртуальное окружение

```bash
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt
```

### Шаг 4: Настройка .env в продакшене

```bash
cp .env.example .env
nano .env

# Минимальный набор
BOT_TOKEN=PROD_TELEGRAM_BOT_TOKEN
BOT_LINK=your_prod_bot_username
REPLICATE_API_TOKEN=PROD_REPLICATE_TOKEN
YOOKASSA_SHOP_ID=PROD_SHOP_ID
YOOKASSA_SECRET_KEY=PROD_SECRET_KEY
ADMIN_IDS=123456789,987654321
DEBUG=false
LOG_LEVEL=INFO
```

### Шаг 5: Инициализация БД на проде

```bash
source venv/bin/activate
python -c "from bot.database.db import Database; import asyncio; asyncio.run(Database.init_db())"

# Проверка
ls -la bot.db
```

### Шаг 6: Тестовый запуск вручную

```bash
source venv/bin/activate
python bot/main.py

# В другом терминале или с телефона проверь /start бота
# Если всё ок — останавливаем Ctrl+C и ставим через systemd
```

### Шаг 7: Настройка systemd сервиса

Создаём юнит:

```bash
sudo nano /etc/systemd/system/interiorbot.service
```

Содержимое:

```ini
[Unit]
Description=InteriorBot Telegram Bot
After=network.target

[Service]
Type=simple
User=%i  # или конкретный пользователь, например: User=interior
WorkingDirectory=/opt/InteriorBot
Environment="PYTHONUNBUFFERED=1"
ExecStart=/opt/InteriorBot/venv/bin/python /opt/InteriorBot/bot/main.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

Перезагрузка systemd и запуск:

```bash
sudo systemctl daemon-reload
sudo systemctl enable interiorbot
sudo systemctl start interiorbot

# Проверка статуса
sudo systemctl status interiorbot
```

Логи:

```bash
journalctl -u interiorbot -f
```

---

## 🐳 Docker-Based Deployment

### Пример Dockerfile

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Устанавливаем зависимости
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Переменные окружения для Python
ENV PYTHONUNBUFFERED=1

CMD ["python", "bot/main.py"]
```

### Пример docker-compose.yml

```yaml
version: "3.9"

services:
  interiorbot:
    build: .
    container_name: interiorbot
    restart: always
    env_file:
      - .env
    volumes:
      - ./bot.db:/app/bot.db  # Пишем БД на хост
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "5"
```

### Сборка и запуск

```bash
# Сборка образа
docker compose build

# Запуск
docker compose up -d

# Логи
docker compose logs -f
```

⚠️ Важно: `.env` должен лежать рядом с `docker-compose.yml` и не попадать в git.

---

## ⚙️ Environment Configuration

### Разделение окружений

Рекомендуется иметь **минимум 2 .env файла**:

- `.env.local` — локальная разработка
- `.env.prod` — продакшн

Пример переключения:

```bash
# Локально
cp .env.local .env
python bot/main.py

# На сервере
cp .env.prod .env
sudo systemctl restart interiorbot
```

### Важные переменные

```env
BOT_TOKEN=...                # Всегда prod-токен для прод-сервера
REPLICATE_API_TOKEN=...      # Prod-токен с нужными лимитами
YOOKASSA_SHOP_ID=...
YOOKASSA_SECRET_KEY=...
ADMIN_IDS=...

DEBUG=false                  # В проде всегда false
LOG_LEVEL=INFO               # Или WARNING/ERROR

# Дополнительно
SENTRY_DSN=...               # Если используете Sentry
```

---

## 📊 Logging & Monitoring

### Минимальная настройка логов

В `bot/main.py`:

```python
import logging
import os

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),          # В stdout (systemd / docker подхватит)
        logging.FileHandler("bot.log"),  # В локальный файл
    ],
)
```

### Просмотр логов

```bash
# systemd
journalctl -u interiorbot -f

# Docker
docker compose logs -f interiorbot

# Локальный файл
tail -f bot.log
```

### Метрики (опционально)

- Sentry — для ошибок
- Grafana + Prometheus — если вынесете метрики в отдельный сервис
- UptimeRobot / Healthchecks — мониторинг доступности

---

## 💾 Backup & Recovery

### Что нужно бэкапить

```text
Обязательно:
- bot.db        # SQLite база данных (пользователи, платежи)

Желательно:
- .env.prod     # Конфигурация и ключи (ИЛИ хранить в секрет-хранилище)
- Логи (bot.log или systemd)
```

### Стратегия бэкапов

```bash
# Простой cron бэкап (раз в день)
crontab -e

# Добавить строку:
0 3 * * * cp /opt/InteriorBot/bot.db /opt/backups/bot_$(date +\%F).db
```

Ротация бэкапов:

```bash
# Удалять старше 7 дней
find /opt/backups -name "bot_*.db" -mtime +7 -delete
```

### Восстановление

```bash
# Остановить бота
sudo systemctl stop interiorbot

# Восстановить БД
cp /opt/backups/bot_2025-12-10.db /opt/InteriorBot/bot.db

# Запустить бота
sudo systemctl start interiorbot
```

---

## 🔒 Security Checklist

### Обязательные меры

```markdown
- [ ] .env НЕ в git и доступен только нужному пользователю
- [ ] Минимальные права на директорию проекта (`chmod 750`)
- [ ] Python запущен под отдельным пользователем (не root)
- [ ] Включен firewall (ufw) и открыт только нужный трафик
- [ ] SSH доступ по ключам, а не паролю
- [ ] Ограничения на количество логов (logrotate / docker json-file options)
```

### Пример настройки UFW

```bash
sudo apt install ufw -y
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp    # SSH
# Если нужен HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
sudo ufw status
```

### Секреты

```markdown
- [ ] BOT_TOKEN хранится только в .env
- [ ] REPLICATE_API_TOKEN не светится в логах
- [ ] YooKassa ключи только в .env
- [ ] Резервные копии .env лежат в зашифрованном хранилище (Vault/1Password)
```

---

## ✅ Deployment Checklist

### Перед первым запуском

```markdown
- [ ] Сервер обновлён (apt update/upgrade)
- [ ] Установлены Python, git, virtualenv
- [ ] Репозиторий склонирован в /opt/InteriorBot
- [ ] venv создан и зависимости установлены
- [ ] .env.prod заполнен и скопирован в .env
- [ ] Database инициализирована (init_db)
- [ ] /start на тестовом аккаунте работает локально
```

### Перед выкладкой в PROD

```markdown
- [ ] Все миграции БД (если были) применены
- [ ] DEBUG=false, LOG_LEVEL=INFO или WARNING
- [ ] Проверены лимиты Replicate и YooKassa
- [ ] Админ-аккаунты проверены (ADMIN_IDS)
- [ ] Логи ротации/размеров настроены
```

### После выкладки

```markdown
- [ ] systemd сервис запущен и активирован (enable + start)
- [ ] Логи не содержат ошибок за первые 10 минут
- [ ] Сделан первый ручной бэкап bot.db
- [ ] Создан cron job на регулярные бэкапы
- [ ] Проверены основные сценарии (см. DEVELOPMENT_GUIDE → Testing)
```

---

**Document Status:** ✅ Complete  
**Last Updated:** December 12, 2025  
**Version:** 2.0 Professional
