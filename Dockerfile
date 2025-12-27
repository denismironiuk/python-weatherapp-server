# -------- Stage 1: Build dependencies --------
FROM python:3.11-slim AS builder

WORKDIR /app

# Копируем только requirements.txt для кеширования слоев
COPY requirements.txt .
# Устанавливаем зависимости в отдельную папку
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt

# Копируем весь код проекта
COPY . /app

# -------- Stage 2: Final lightweight image --------
FROM python:3.11-slim

# Устанавливаем curl для Healthcheck
RUN apt-get update && apt-get install -y curl && apt-get clean

# Создаем пользователя для безопасности
RUN useradd -m den4ik

WORKDIR /app

# Копируем установленные библиотеки и код из builder
COPY --from=builder /install /usr/local
COPY --from=builder /app /app

# Права доступа для пользователя den4ik
RUN chown -R den4ik:den4ik /app

USER den4ik

# Healthcheck — ОЧЕНЬ ВАЖНО: убедись, что у тебя есть роут /health в Flask
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://127.0.0.1:5000/health || exit 1

# Запуск приложения через Gunicorn
# application — это имя твоего файла application.py
# app — это имя переменной app = Flask(__name__)
CMD ["gunicorn", "application:app", "--workers=3", "--bind=0.0.0.0:5000"]