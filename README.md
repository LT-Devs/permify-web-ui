# Permify API Manager

Permify API Manager - это приложение для управления схемами и отношениями в системе авторизации [Permify](https://github.com/Permify/permify).

## Особенности

- **Два режима работы**: 
  - **Упрощенный** для администраторов системы - работа с пользователями, группами и приложениями
  - **Ручной** для разработчиков - прямая работа со схемами, отношениями и проверка разрешений

- **Управление пользователями**:
  - Создание пользователей
  - Добавление пользователей в группы
  - Назначение ролей в приложениях

- **Управление группами**:
  - Создание групп
  - Управление участниками групп
  - Предоставление доступа к приложениям

- **Управление приложениями**:
  - Создание новых приложений с настраиваемыми действиями
  - Настройка разрешений для разных ролей
  - Назначение пользователей и групп
  - Проверка разрешений

- **Работа со схемами**:
  - Загрузка схем из файлов
  - Создание схем вручную
  - Просмотр и управление версиями схем

- **Работа с отношениями**:
  - Просмотр существующих отношений
  - Создание новых отношений
  - Удаление отношений

- **Проверка разрешений**:
  - Проверка доступа пользователей к ресурсам
  - Просмотр детальной информации о решении

## Системные требования

- Python 3.8 или выше
- Streamlit 1.45.0 или выше
- Permify сервер (локальный или удаленный)

## Установка

1. Клонируйте репозиторий:
```
git clone https://github.com/yourusername/permify-api-manager.git
cd permify-api-manager
```

2. Установите зависимости:
```
pip install -r requirements.txt
```

3. Настройте переменные окружения:
```
export PERMIFY_HOST=http://localhost:9010
export PERMIFY_GRPC_HOST=http://localhost:9011
export PERMIFY_TENANT=t1
```

## Использование

Запустите приложение:
```
streamlit run permify_app_v2.py
```

Или, для использования исходной версии приложения:
```
streamlit run permify_app.py
```

## Архитектура приложения

Приложение реализовано с использованием паттерна MVC (Model-View-Controller):

- **Models**: Отвечают за взаимодействие с API Permify
- **Views**: Отвечают за отображение информации пользователю
- **Controllers**: Управляют моделями и представлениями

## Структура проекта

```
permify-api-manager/
├── app/
│   ├── models/
│   │   ├── __init__.py
│   │   ├── base_model.py
│   │   ├── schema_model.py
│   │   ├── relationship_model.py
│   │   ├── user_model.py
│   │   ├── group_model.py
│   │   └── app_model.py
│   ├── views/
│   │   ├── __init__.py
│   │   ├── base_view.py
│   │   ├── user_view.py
│   │   ├── group_view.py
│   │   ├── app_view.py
│   │   ├── schema_view.py
│   │   ├── relationship_view.py
│   │   ├── permission_check_view.py
│   │   └── status_view.py
│   ├── controllers/
│   │   ├── __init__.py
│   │   ├── base_controller.py
│   │   ├── schema_controller.py
│   │   ├── relationship_controller.py
│   │   ├── user_controller.py
│   │   ├── group_controller.py
│   │   └── app_controller.py
│   ├── __init__.py
│   └── main.py
├── permify_app_v2.py
├── permify_app.py
├── requirements.txt
└── README.md
```

## Лицензия

MIT 