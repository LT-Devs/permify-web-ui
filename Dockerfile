FROM python:3.13-slim

WORKDIR /app

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY wheels /app/wheels
COPY requirements.txt .
RUN pip install --no-index --find-links=/app/wheels -r requirements.txt


# Копирование приложения
COPY . .

# Делаем скрипты исполняемыми
RUN chmod +x *.py

# Порт для Streamlit
EXPOSE 8501

# Запускаем приложение
CMD ["python", "run.py"] 