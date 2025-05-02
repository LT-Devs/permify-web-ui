FROM python:3.9-slim

WORKDIR /app

# Установка зависимостей
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    git \
    && rm -rf /var/lib/apt/lists/*

# Установка Python зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копирование приложения
COPY . .

# Делаем скрипты исполняемыми
RUN chmod +x *.py

# Порт для Streamlit
EXPOSE 8501

# Запускаем Streamlit приложение
CMD ["streamlit", "run", "permify_app.py", "--server.port=8501", "--server.address=0.0.0.0"] 