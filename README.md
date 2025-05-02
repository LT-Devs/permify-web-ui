# Permify API Manager

Управление схемами авторизации и отношениями для Permify через веб-интерфейс.

## Описание

Это приложение предоставляет веб-интерфейс для управления схемами и отношениями в системе авторизации Permify. Оно позволяет:

- Загружать и создавать схемы авторизации
- Создавать отношения между сущностями
- Проверять доступы

## Установка и запуск

### Вариант 1: Запуск с помощью виртуального окружения Python

1. Создайте виртуальное окружение и активируйте его:
   ```bash
   python -m venv permify_venv
   source permify_venv/bin/activate
   ```

2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```

3. Запустите Permify с помощью docker-compose:
   ```bash
   docker-compose up -d
   ```

4. Запустите веб-интерфейс:
   ```bash
   streamlit run permify_app.py
   ```

5. Откройте браузер по адресу http://localhost:8501

### Вариант 2: Запуск с помощью Docker

1. Соберите и запустите все сервисы с помощью docker-compose:
   ```bash
   docker-compose -f docker-compose-ui.yml up -d
   ```

2. Откройте браузер по адресу http://localhost:8501 или http://permify-ui.locator (если настроен Traefik)

## Примеры использования

### Загрузка схемы

1. В Streamlit интерфейсе выберите в меню слева "Схемы"
2. Укажите путь к файлу схемы или введите схему вручную
3. Нажмите "Загрузить схему" и затем "Создать схему в Permify"

### Создание отношений

1. В Streamlit интерфейсе выберите в меню слева "Отношения"
2. Введите данные отношения или используйте пакетное создание
3. Нажмите "Создать отношение" или "Создать пакет отношений"

## Примеры отношений

Пример отношений из таблицы:
```
oodiks	1	admin	user	1
garrison	1	assigned	user	1
petitions	*	reader	user	1
```

## Структура проекта

- `permify_app.py` - основное приложение Streamlit
- `permify_grpc_client.py` - клиент для работы с gRPC API Permify
- `permify_cli.py` - утилита для взаимодействия с CLI Permify через Docker
- `schema.perm` - пример схемы авторизации
- `relationships.json` - пример отношений в формате JSON
- `Dockerfile` - файл для сборки Docker образа
- `docker-compose.yml` - конфигурация для запуска Permify
- `docker-compose-ui.yml` - конфигурация для запуска Permify с веб-интерфейсом 