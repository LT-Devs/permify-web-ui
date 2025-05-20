FROM python:3.13-slim AS builder

WORKDIR /app

# Копируем только файлы для установки
COPY requirements.txt .
# Устанавливаем зависимости, копируем только то что нужно
COPY wheels /app/wheels
RUN pip install --no-index --find-links=/app/wheels -r requirements.txt \
    && rm -rf /app/wheels

# Многоступенчатая сборка - финальный образ
FROM python:3.13-slim

WORKDIR /app

# Копируем только необходимые файлы из первого этапа
COPY --from=builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
# Копируем только необходимые файлы приложения
COPY app/ ./app/
COPY *.py ./
COPY requirements.txt ./

# Делаем скрипты исполняемыми
RUN chmod +x *.py

# Порт для Streamlit
EXPOSE 8501

# Запускаем приложение
CMD ["python", "run.py"] 