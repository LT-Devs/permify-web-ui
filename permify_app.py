import streamlit as st
import requests
import json
import time
import os
import tempfile
import subprocess
import io
from pathlib import Path
import pandas as pd

# Настройки Permify API из переменных окружения
PERMIFY_HOST = os.environ.get("PERMIFY_HOST", "http://localhost:9010")
PERMIFY_GRPC_HOST = os.environ.get("PERMIFY_GRPC_HOST", "http://localhost:9011")
DEFAULT_TENANT = os.environ.get("PERMIFY_TENANT", "t1")

# Заголовок приложения
st.title("Permify API Manager")
st.sidebar.header("Управление")

# Для отладки показываем используемые хосты
st.sidebar.write(f"API Host: {PERMIFY_HOST}")
st.sidebar.write(f"gRPC Host: {PERMIFY_GRPC_HOST}")

# Функция для выбора файлов на сервере
def server_file_selector(folder_path='.', extensions=None):
    try:
        files = []
        for item in Path(folder_path).glob('**/*'):
            if item.is_file():
                if extensions is None or item.suffix.lower().lstrip('.') in extensions:
                    files.append(str(item))
        
        if not files:
            st.warning(f"В директории {folder_path} не найдено файлов" + 
                       (f" с расширениями: {', '.join(extensions)}" if extensions else ""))
            return None
            
        selected_file = st.selectbox('Выберите файл', sorted(files))
        return selected_file
    except Exception as e:
        st.error(f"Ошибка при сканировании файлов: {str(e)}")
        return None

# Функция для проверки статуса Permify
def check_permify_status():
    try:
        response = requests.get(f"{PERMIFY_HOST}/healthz")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "SERVING":
                return True, "Сервер работает"
        return False, f"Ошибка статуса: {response.text}"
    except Exception as e:
        return False, f"Ошибка соединения: {str(e)}"

# Функция для загрузки схемы из файла
def load_schema_from_file(file_path):
    try:
        with open(file_path, 'r') as f:
            schema_content = f.read()
        return schema_content
    except Exception as e:
        st.error(f"Ошибка при чтении файла: {str(e)}")
        return None

# Функция для получения текущей схемы
def get_current_schema(tenant_id=DEFAULT_TENANT, schema_version=None):
    try:
        # Сначала получаем список схем
        list_endpoint = f"{PERMIFY_HOST}/v1/tenants/{tenant_id}/schemas/list"
        
        list_data = {
            "page_size": 50,  # Получаем больше схем для полного списка
            "continuous_token": ""
        }
        
        list_response = requests.post(
            list_endpoint,
            json=list_data,
            headers={"Content-Type": "application/json"}
        )
        
        if list_response.status_code != 200:
            return False, f"Ошибка получения списка схем: {list_response.text}"
        
        schemas_list = list_response.json()
        
        # Проверяем, есть ли схемы в списке
        if not schemas_list.get("schemas") or len(schemas_list["schemas"]) == 0:
            return False, "Нет доступных схем"
        
        # Сортируем схемы по дате создания (новые сначала)
        sorted_schemas = sorted(schemas_list["schemas"], 
                               key=lambda x: x.get('created_at', ''), 
                               reverse=True)
        
        # Если указана конкретная версия, используем её
        if schema_version:
            # Находим схему с указанной версией
            target_schema = None
            for schema in sorted_schemas:
                if schema.get("version") == schema_version:
                    target_schema = schema
                    break
            
            if not target_schema:
                return False, f"Схема с версией {schema_version} не найдена"
                
            version_to_use = schema_version
        else:
            # Иначе используем самую новую версию (первую в отсортированном списке)
            version_to_use = sorted_schemas[0]["version"]
        
        # Теперь получаем детальную информацию о схеме
        read_endpoint = f"{PERMIFY_HOST}/v1/tenants/{tenant_id}/schemas/read"
        
        read_data = {
            "metadata": {
                "schema_version": version_to_use
            }
        }
        
        read_response = requests.post(
            read_endpoint,
            json=read_data,
            headers={"Content-Type": "application/json"}
        )
        
        if read_response.status_code == 200:
            result = read_response.json()
            # Добавляем версию схемы к результату
            result["version"] = version_to_use
            # Добавляем список всех доступных версий
            result["available_versions"] = [{"version": s["version"], "created_at": s["created_at"]} for s in sorted_schemas]
            return True, result
        else:
            return False, f"Ошибка при получении схемы: {read_response.text}"
    
    except Exception as e:
        import traceback
        return False, f"Ошибка: {str(e)}\nТрассировка: {traceback.format_exc()}"

# Функция для создания схемы
def create_schema(schema_content, tenant_id=DEFAULT_TENANT):
    try:
        # Используем только один эндпоинт для создания схемы
        endpoint = f"{PERMIFY_HOST}/v1/tenants/{tenant_id}/schemas/write"
        
        # Формируем JSON с полем schema и метаданными
        data = {
            "schema": schema_content
        }
        
        # Отправляем схему как JSON
        response = requests.post(
            endpoint,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            st.success(f"Схема успешно создана: {response.text}")
            return True
        else:
            st.warning(f"Ошибка при создании схемы: {response.text}")
            # Дополнительная информация для отладки
            st.info(f"Конечная точка: {endpoint}")
            st.info(f"Код ответа: {response.status_code}")
            st.info(f"Содержимое схемы: {schema_content[:100]}...")
            return False
    except Exception as e:
        st.error(f"Ошибка при создании схемы: {str(e)}")
        return False

# Функция для валидации схемы через API
def validate_schema(schema_content):
    try:
        # Создаем временный файл для схемы
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.perm') as f:
            f.write(schema_content)
            temp_file = f.name
        
        # Пробуем использовать validate API
        endpoints = [
            f"{PERMIFY_HOST}/v1/schemas/validate",
            f"{PERMIFY_HOST}/v1/tenants/{DEFAULT_TENANT}/schemas/validate"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.post(
                    endpoint,
                    data=schema_content,
                    headers={"Content-Type": "text/plain"}
                )
                
                if response.status_code == 200:
                    # Удаляем временный файл
                    os.unlink(temp_file)
                    return True, "Схема валидна"
                elif response.status_code != 404:
                    # Удаляем временный файл
                    os.unlink(temp_file)
                    return False, f"Ошибка валидации: {response.text}"
            except Exception as e:
                pass  # Пробуем следующий эндпоинт
        
        # Если API не работает, пробуем локальную валидацию
        try:
            # Проверим синтаксис схемы без Docker
            # Минимальная валидация - проверим на базовый синтаксис
            valid = True
            errors = []
            
            lines = schema_content.strip().split('\n')
            brackets_count = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith('//'):
                    continue
                
                brackets_count += line.count('{') - line.count('}')
                
                if 'entity' in line and '{' not in line and i < len(lines) - 1 and '{' not in lines[i + 1]:
                    valid = False
                    errors.append(f"Строка {i+1}: Ожидается открывающая скобка {{ после объявления entity")
            
            if brackets_count != 0:
                valid = False
                errors.append(f"Несбалансированные скобки: {brackets_count}")
                
            # Удаляем временный файл
            os.unlink(temp_file)
            
            if valid:
                return True, "Схема прошла базовую валидацию"
            else:
                return False, "Ошибки в схеме: " + "; ".join(errors)
                
        except Exception as e:
            # Удаляем временный файл
            os.unlink(temp_file)
            return False, f"Ошибка при валидации: {str(e)}"
    
    except Exception as e:
        return False, f"Ошибка при валидации: {str(e)}"

# Функция для создания отношений
def create_relationship(entity_type, entity_id, relation, subject_type, subject_id, tenant_id=DEFAULT_TENANT):
    try:
        # Формируем данные для отношения согласно документации
        data = {
            "metadata": {
                "schema_version": ""  # Обязательное поле, даже если пустое
            },
            "tuples": [
                {
                    "entity": {"type": entity_type, "id": entity_id},
                    "relation": relation,
                    "subject": {
                        "type": subject_type, 
                        "id": subject_id,
                        "relation": ""  # Может быть пустым, но должно быть указано
                    }
                }
            ]
        }
        
        # Используем правильный эндпоинт для записи отношений
        endpoint = f"{PERMIFY_HOST}/v1/tenants/{tenant_id}/data/write"
        
        response = requests.post(
            endpoint,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return True, response.text
        else:
            return False, f"Ошибка создания отношения: {response.text}"
    except Exception as e:
        return False, f"Ошибка: {str(e)}"

# Функция для получения всех отношений
def get_relationships(tenant_id=DEFAULT_TENANT):
    try:
        # Используем правильный эндпоинт для чтения отношений
        endpoint = f"{PERMIFY_HOST}/v1/tenants/{tenant_id}/data/relationships/read"
        
        # Формируем запрос без фильтра, чтобы получить все отношения
        data = {
            "metadata": {
                "snap_token": ""
            },
            "filter": {
                # Оставляем фильтр пустым, чтобы получить все отношения
            },
            "page_size": 100  # Можно настроить размер страницы
        }
        
        response = requests.post(
            endpoint,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return True, response.json()
        else:
            return False, f"Ошибка получения отношений: {response.text}"
    except Exception as e:
        return False, f"Ошибка: {str(e)}"

# Добавляем функцию для удаления отношения
def delete_relationship(entity_type, entity_id, relation, subject_type, subject_id, tenant_id=DEFAULT_TENANT):
    try:
        # Формируем запрос на удаление отношения согласно документации API
        data = {
            "metadata": {
                "snap_token": ""
            },
            "tuple_filter": {
                "entity": {
                    "type": entity_type,
                    "ids": [entity_id]
                },
                "relation": relation,
                "subject": {
                    "type": subject_type,
                    "ids": [subject_id],
                    "relation": ""
                }
            },
            "attribute_filter": {}  # Добавлено согласно документации API
        }
        
        # Используем правильный эндпоинт для удаления данных
        endpoint = f"{PERMIFY_HOST}/v1/tenants/{tenant_id}/data/delete"
        
        response = requests.post(
            endpoint,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            return True, "Отношение успешно удалено"
        else:
            return False, f"Ошибка удаления отношения: {response.text}"
    except Exception as e:
        return False, f"Ошибка: {str(e)}"

# Добавляем функцию для пакетного удаления отношений
def delete_multiple_relationships(relationships, tenant_id=DEFAULT_TENANT):
    results = []
    success_count = 0
    error_count = 0
    
    for rel in relationships:
        entity_type = rel.get("entity_type")
        entity_id = rel.get("entity_id")
        relation = rel.get("relation")
        subject_type = rel.get("subject_type")
        subject_id = rel.get("subject_id")
        
        success, message = delete_relationship(
            entity_type, entity_id, relation, subject_type, subject_id, tenant_id
        )
        
        if success:
            success_count += 1
        else:
            error_count += 1
            results.append(f"Ошибка удаления {entity_type}:{entity_id} → {relation} → {subject_type}:{subject_id}: {message}")
    
    return success_count, error_count, results

# Функция для проверки доступа
def check_permission(entity_type, entity_id, permission, user_id, tenant_id=DEFAULT_TENANT, schema_version=None):
    try:
        # Если версия схемы не указана, получаем последнюю версию схемы
        if not schema_version:
            # Получаем список схем
            list_endpoint = f"{PERMIFY_HOST}/v1/tenants/{tenant_id}/schemas/list"
            list_data = {
                "page_size": 50,  # Получаем больше схем для полного списка
                "continuous_token": ""
            }
            
            list_response = requests.post(
                list_endpoint,
                json=list_data,
                headers={"Content-Type": "application/json"}
            )
            
            if list_response.status_code != 200:
                return False, f"Ошибка получения списка схем: {list_response.text}"
            
            schemas_list = list_response.json()
            
            # Проверяем, есть ли схемы в списке
            if not schemas_list.get("schemas") or len(schemas_list["schemas"]) == 0:
                return False, "Нет доступных схем. Сначала создайте схему."
            
            # Сортируем схемы по дате создания (новые сначала)
            sorted_schemas = sorted(schemas_list["schemas"], 
                                  key=lambda x: x.get('created_at', ''), 
                                  reverse=True)
            
            # Получаем самую новую версию схемы (первая в отсортированном списке)
            schema_version = sorted_schemas[0]["version"]
        
        # Показываем информацию о выбранной версии схемы
        st.info(f"Используется версия схемы: {schema_version}")
        
        # Формируем запрос на проверку разрешения согласно документации
        data = {
            "metadata": {
                "snap_token": "",
                "schema_version": schema_version,  # Используем указанную версию схемы
                "depth": 20
            },
            "entity": {"type": entity_type, "id": entity_id},
            "permission": permission,
            "subject": {
                "type": "user", 
                "id": user_id,
                "relation": ""
            }
        }
        
        # Используем правильный эндпоинт для проверки доступа
        endpoint = f"{PERMIFY_HOST}/v1/tenants/{tenant_id}/permissions/check"
        
        response = requests.post(
            endpoint,
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            return True, result
        else:
            return False, f"Ошибка проверки доступа: {response.text}"
    except Exception as e:
        import traceback
        return False, f"Ошибка: {str(e)}\nТрассировка: {traceback.format_exc()}"

# Проверка статуса Permify
status, message = check_permify_status()
if status:
    st.sidebar.success("✅ Permify доступен")
else:
    st.sidebar.error(f"❌ Permify недоступен: {message}")

# Секции в боковой панели
menu = st.sidebar.selectbox(
    "Выберите действие",
    ["Схемы", "Отношения", "Проверка доступа", "Статус системы"]
)

# Загрузка и создание схемы
if menu == "Схемы":
    st.header("Управление схемами")
    
    # Выбор арендатора
    tenant_id = st.text_input("ID арендатора", DEFAULT_TENANT)
    
    # Показываем все версии схем
    st.subheader("Версии схем")
    
    if st.button("Получить все версии схем"):
        try:
            # Получаем список всех схем
            list_endpoint = f"{PERMIFY_HOST}/v1/tenants/{tenant_id}/schemas/list"
            list_data = {
                "page_size": 50,  # Увеличиваем количество получаемых схем
                "continuous_token": ""
            }
            
            list_response = requests.post(
                list_endpoint,
                json=list_data,
                headers={"Content-Type": "application/json"}
            )
            
            if list_response.status_code != 200:
                st.error(f"Ошибка получения списка схем: {list_response.text}")
            else:
                schemas_list = list_response.json()
                
                # Проверяем, есть ли схемы в списке
                if not schemas_list.get("schemas") or len(schemas_list["schemas"]) == 0:
                    st.warning("Нет доступных схем. Сначала создайте схему.")
                else:
                    # Сортируем схемы по дате создания, чтобы самая новая была первой
                    sorted_schemas = sorted(schemas_list['schemas'], 
                                          key=lambda x: x.get('created_at', ''), 
                                          reverse=True)
                    
                    # Отображаем карточки схем
                    st.write(f"Найдено версий схем: {len(sorted_schemas)}")
                    
                    # Показываем информацию о последней версии
                    st.success(f"Последняя версия схемы: {sorted_schemas[0]['version']} (создана: {sorted_schemas[0]['created_at']})")
                    
                    # Создаем таблицу для версий схем
                    schema_data = []
                    for schema in sorted_schemas:
                        schema_data.append({
                            "Версия": schema.get("version", ""),
                            "Дата создания": schema.get("created_at", ""),
                        })
                    
                    # Отображаем таблицу версий
                    st.table(pd.DataFrame(schema_data))
                    
                    # Создаем вкладки для отображения схем
                    for i, schema in enumerate(sorted_schemas):
                        with st.expander(f"Схема версии {schema['version']} (создана: {schema['created_at']})"):
                            # Создаем кнопку для просмотра этой версии схемы
                            schema_version = schema['version']
                            if st.button(f"Просмотреть", key=f"view_schema_{schema_version}"):
                                try:
                                    # Получаем детальную информацию о схеме
                                    read_endpoint = f"{PERMIFY_HOST}/v1/tenants/{tenant_id}/schemas/read"
                                    read_data = {
                                        "metadata": {
                                            "schema_version": schema_version
                                        }
                                    }
                                    
                                    read_response = requests.post(
                                        read_endpoint,
                                        json=read_data,
                                        headers={"Content-Type": "application/json"}
                                    )
                                    
                                    if read_response.status_code == 200:
                                        schema_content = read_response.json()
                                        st.json(schema_content)
                                        
                                        # Если есть данные о схеме, попробуем отобразить их в более читаемом виде
                                        if 'schema' in schema_content:
                                            st.subheader("Содержимое схемы:")
                                            if 'entityDefinitions' in schema_content['schema']:
                                                entities = schema_content['schema']['entityDefinitions']
                                                entity_data = []
                                                for entity_name, entity_def in entities.items():
                                                    permissions = list(entity_def.get('permissions', {}).keys())
                                                    relations = list(entity_def.get('relations', {}).keys())
                                                    entity_data.append({
                                                        "Сущность": entity_name,
                                                        "Отношения": ", ".join(relations) if relations else "-",
                                                        "Разрешения": ", ".join(permissions) if permissions else "-"
                                                    })
                                                
                                                if entity_data:
                                                    st.table(pd.DataFrame(entity_data))
                                    else:
                                        st.error(f"Ошибка при получении схемы {schema_version}: {read_response.text}")
                                except Exception as e:
                                    st.error(f"Ошибка при просмотре схемы: {str(e)}")
        except Exception as e:
            st.error(f"Ошибка: {str(e)}")
    
    # Показываем текущую (последнюю) схему
    st.subheader("Текущая схема")
    if st.button("Получить текущую схему"):
        success, result = get_current_schema(tenant_id)
        if success:
            st.json(result)
            
            # Если есть данные о схеме, отображаем их в более читаемом виде
            if 'schema' in result:
                st.subheader("Сущности в схеме:")
                if 'entityDefinitions' in result['schema']:
                    for entity_name, entity_def in result['schema']['entityDefinitions'].items():
                        st.write(f"- {entity_name}")
                        
                        # Показываем отношения для этой сущности
                        if 'relations' in entity_def:
                            st.write(f"  Отношения:")
                            for relation_name, relation_def in entity_def['relations'].items():
                                st.write(f"  - {relation_name}")
                        
                        # Показываем разрешения для этой сущности
                        if 'permissions' in entity_def:
                            st.write(f"  Разрешения:")
                            for perm_name in entity_def['permissions'].keys():
                                st.write(f"  - {perm_name}")
        else:
            st.error(result)
    
    # Загрузка схемы
    st.subheader("Загрузка схемы")
    
    upload_type = st.radio(
        "Способ загрузки схемы",
        ["Загрузить файл с компьютера", "Выбрать файл на сервере", "Ввести схему вручную"]
    )
    
    if upload_type == "Загрузить файл с компьютера":
        uploaded_file = st.file_uploader("Выберите файл схемы", type=["perm"], accept_multiple_files=False)
        
        if uploaded_file is not None:
            # Чтение содержимого файла
            schema_content = uploaded_file.getvalue().decode("utf-8")
            st.code(schema_content, language="perm")
            
            # Валидация схемы
            is_valid, validation_msg = validate_schema(schema_content)
            if is_valid:
                st.success("✅ Схема валидна")
                if st.button("Создать схему в Permify"):
                    create_schema(schema_content, tenant_id)
            else:
                st.error(f"❌ {validation_msg}")
    
    elif upload_type == "Выбрать файл на сервере":
        # Опция выбора директории
        base_dir = st.text_input("Базовая директория", value=".")
        schema_file = server_file_selector(base_dir, extensions=["perm"])
        
        if schema_file:
            schema_content = load_schema_from_file(schema_file)
            if schema_content:
                st.code(schema_content, language="perm")
                
                # Валидация схемы
                is_valid, validation_msg = validate_schema(schema_content)
                if is_valid:
                    st.success("✅ Схема валидна")
                    if st.button("Создать схему в Permify"):
                        create_schema(schema_content, tenant_id)
                else:
                    st.error(f"❌ {validation_msg}")
    
    elif upload_type == "Ввести схему вручную":
        manual_schema = st.text_area("Введите схему вручную", height=300)
        
        if manual_schema:
            # Кнопка для валидации схемы
            if st.button("Валидировать схему"):
                is_valid, validation_msg = validate_schema(manual_schema)
                if is_valid:
                    st.success("✅ Схема валидна")
                else:
                    st.error(f"❌ {validation_msg}")
        
            if st.button("Создать схему из текста"):
                if manual_schema:
                    # Сначала валидируем
                    is_valid, validation_msg = validate_schema(manual_schema)
                    if is_valid:
                        create_schema(manual_schema, tenant_id)
                    else:
                        st.error(f"❌ {validation_msg}")
                else:
                    st.warning("Введите схему перед созданием")

# Управление отношениями
elif menu == "Отношения":
    st.header("Управление отношениями")
    
    # Выбор арендатора
    tenant_id = st.text_input("ID арендатора", DEFAULT_TENANT)
    
    # Показываем текущие отношения
    st.subheader("Текущие отношения")
    
    # Создаем контейнер для отображения сообщений об удалении
    delete_message_container = st.empty()
    
    # Хранение состояния для выбранных отношений
    if 'selected_relations' not in st.session_state:
        st.session_state.selected_relations = []
    
    # Функция для обработки выбора строк
    def handle_selection(rows):
        st.session_state.selected_relations = rows
    
    # Получаем все отношения при открытии страницы или при нажатии кнопки
    if st.button("Обновить отношения") or 'relationships_loaded' not in st.session_state:
        success, result = get_relationships(tenant_id)
        if success:
            st.session_state.relationship_result = result
            st.session_state.relationships_loaded = True
        else:
            st.error(result)
    
    # Если отношения загружены, показываем их
    if 'relationship_result' in st.session_state:
        tuples = st.session_state.relationship_result.get("tuples", [])
        if tuples:
            # Создаем DataFrame для отображения отношений
            relation_data = []
            for tuple_data in tuples:
                entity = tuple_data.get("entity", {})
                subject = tuple_data.get("subject", {})
                relation = tuple_data.get("relation", "")
                
                relation_data.append({
                    "Тип сущности": entity.get("type", ""),
                    "ID сущности": entity.get("id", ""),
                    "Отношение": relation,
                    "Тип субъекта": subject.get("type", ""),
                    "ID субъекта": subject.get("id", ""),
                    "Полное отношение": f"{entity.get('type')}:{entity.get('id')} → {relation} → {subject.get('type')}:{subject.get('id')}",
                    "entity_type": entity.get("type", ""),
                    "entity_id": entity.get("id", ""),
                    "relation": relation,
                    "subject_type": subject.get("type", ""),
                    "subject_id": subject.get("id", "")
                })
            
            # Создаем и отображаем интерактивную таблицу с возможностью выбора строк
            if relation_data:
                df = pd.DataFrame(relation_data)
                
                # Отображаем только видимые столбцы, но сохраняем в DataFrame все данные для удаления
                display_df = df[["Тип сущности", "ID сущности", "Отношение", "Тип субъекта", "ID субъекта", "Полное отношение"]]
                
                # Отображаем таблицу с выбором строк
                selected_indices = []
                
                # Опции для выбора строк
                st.info("Выберите отношения для удаления, используя чекбоксы слева")
                
                # Создаем селекторы для каждой строки
                selected_rows = []
                for i, row in display_df.iterrows():
                    col1, col2 = st.columns([1, 20])
                    with col1:
                        is_selected = st.checkbox("", key=f"select_{i}", value=False)
                        if is_selected:
                            selected_rows.append({
                                "entity_type": df.iloc[i]["entity_type"],
                                "entity_id": df.iloc[i]["entity_id"],
                                "relation": df.iloc[i]["relation"],
                                "subject_type": df.iloc[i]["subject_type"],
                                "subject_id": df.iloc[i]["subject_id"]
                            })
                    with col2:
                        st.text(row["Полное отношение"])
                
                # Кнопка для удаления выбранных отношений
                if selected_rows:
                    if st.button(f"Удалить выбранные отношения ({len(selected_rows)})", type="primary"):
                        success_count, error_count, errors = delete_multiple_relationships(selected_rows, tenant_id)
                        
                        if success_count > 0:
                            delete_message_container.success(f"Успешно удалено отношений: {success_count}")
                            # Перезагружаем данные
                            success, result = get_relationships(tenant_id)
                            if success:
                                st.session_state.relationship_result = result
                                st.rerun()  # Перезагружаем страницу для обновления списка
                        
                        if error_count > 0:
                            delete_message_container.error(f"Ошибок при удалении: {error_count}")
                            for error in errors:
                                st.write(error)
            else:
                st.info("Отношения не найдены")
        else:
            st.info("Отношения не найдены")

    # Добавляем раздел для создания нового отношения
    st.subheader("Создать новое отношение")
    
    col1, col2 = st.columns(2)
    
    with col1:
        new_entity_type = st.text_input("Тип сущности", "document")
        new_entity_id = st.text_input("ID сущности", "1")
        new_relation = st.text_input("Отношение", "owner")
    
    with col2:
        new_subject_type = st.text_input("Тип субъекта", "user")
        new_subject_id = st.text_input("ID субъекта", "1")
    
    if st.button("Создать отношение"):
        success, message = create_relationship(
            new_entity_type, new_entity_id, new_relation, new_subject_type, new_subject_id, tenant_id
        )
        if success:
            st.success(f"Отношение успешно создано: {message}")
            # Обновляем данные
            success, result = get_relationships(tenant_id)
            if success:
                st.session_state.relationship_result = result
                st.rerun()  # Перезагружаем страницу для обновления списка
        else:
            st.error(message)

# Проверка доступа
elif menu == "Проверка доступа":
    st.header("Проверка доступа")
    
    # Выбор арендатора
    tenant_id = st.text_input("ID арендатора", DEFAULT_TENANT)
    
    # Получаем список доступных схем
    list_endpoint = f"{PERMIFY_HOST}/v1/tenants/{tenant_id}/schemas/list"
    
    list_data = {
        "page_size": 50,
        "continuous_token": ""
    }
    
    list_response = requests.post(
        list_endpoint,
        json=list_data,
        headers={"Content-Type": "application/json"}
    )
    
    # Переменная для хранения выбранной версии схемы
    selected_schema_version = None
    
    if list_response.status_code == 200:
        schemas_list = list_response.json()
        if schemas_list.get("schemas") and len(schemas_list["schemas"]) > 0:
            # Сортируем схемы по дате создания (новые сначала)
            sorted_schemas = sorted(schemas_list["schemas"], 
                                   key=lambda x: x.get('created_at', ''), 
                                   reverse=True)
            
            # Предлагаем выбор версии схемы
            schema_options = [f"{schema.get('version')} (создана: {schema.get('created_at')})" for schema in sorted_schemas]
            schema_option = st.selectbox("Выберите версию схемы", ["Последняя версия"] + schema_options)
            
            if schema_option != "Последняя версия":
                # Извлекаем версию схемы из выбранной опции
                selected_schema_version = schema_option.split()[0]
    
    # Получаем текущую схему для показа доступных типов сущностей и разрешений
    success, schema_result = get_current_schema(tenant_id, selected_schema_version)
    
    # Информация о текущей схеме
    if success and isinstance(schema_result, dict):
        st.success(f"Загружена схема версии: {schema_result.get('version')}")
    
    # Получаем все отношения
    rel_success, rel_result = get_relationships(tenant_id)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Если схема успешно получена, предлагаем выбор из доступных в схеме типов
        if success and isinstance(schema_result, dict) and "schema" in schema_result:
            try:
                entity_types = list(schema_result["schema"].get("entityDefinitions", {}).keys())
                if entity_types:
                    entity_type = st.selectbox("Тип сущности", entity_types, index=entity_types.index("petitions") if "petitions" in entity_types else 0)
                else:
                    entity_type = st.text_input("Тип сущности", "petitions")
            except Exception as e:
                st.warning(f"Не удалось получить типы сущностей из схемы: {str(e)}")
                entity_type = st.text_input("Тип сущности", "petitions")
        else:
            entity_type = st.text_input("Тип сущности", "petitions")
        
        entity_id = st.text_input("ID сущности", "1")
        
        # Если схема успешно получена, предлагаем выбор из доступных в схеме разрешений
        if success and isinstance(schema_result, dict) and "schema" in schema_result:
            try:
                entity_def = schema_result["schema"].get("entityDefinitions", {}).get(entity_type, {})
                permissions = list(entity_def.get("permissions", {}).keys())
                if permissions:
                    permission = st.selectbox("Разрешение", permissions)
                else:
                    permission = st.text_input("Разрешение", "read")
            except Exception as e:
                st.warning(f"Не удалось получить разрешения из схемы: {str(e)}")
                permission = st.text_input("Разрешение", "read")
        else:
            permission = st.text_input("Разрешение", "read")
    
    with col2:
        user_id = st.text_input("ID пользователя", "1")
    
    # Если схема успешно получена, показываем доступные типы сущностей и разрешения
    if success:
        try:
            st.subheader("Доступные типы сущностей и разрешения")
            if isinstance(schema_result, dict) and "schema" in schema_result:
                entities = schema_result.get("schema", {}).get("entityDefinitions", {})
                
                # Создаем таблицу для более наглядного отображения
                entity_permissions = []
                
                for entity_name, entity_data in entities.items():
                    permissions = entity_data.get("permissions", {})
                    if permissions:
                        perm_names = ", ".join(permissions.keys())
                        entity_permissions.append({
                            "Сущность": entity_name,
                            "Разрешения": perm_names
                        })
                        
                        # Показываем логику разрешений для большей ясности
                        with st.expander(f"Подробности о {entity_name}"):
                            for perm_name, perm_details in permissions.items():
                                if 'child' in perm_details:
                                    expr = perm_details.get('child', {}).get('stringExpr', '')
                                    if expr:
                                        st.info(f"⚙️ {entity_name}.{perm_name} = {expr}")
                
                if entity_permissions:
                    st.table(pd.DataFrame(entity_permissions))
            else:
                st.warning("Схема имеет неожиданный формат")
                st.json(schema_result)
        except Exception as e:
            st.warning(f"Не удалось показать доступные типы: {str(e)}")
    
    # Если отношения успешно получены, показываем их
    if rel_success:
        try:
            st.subheader("Существующие отношения")
            tuples = rel_result.get("tuples", [])
            
            # Фильтруем отношения для текущего пользователя
            user_tuples = [t for t in tuples if t.get("subject", {}).get("type") == "user" and 
                            t.get("subject", {}).get("id") == user_id]
            
            # Показываем отдельно отношения для текущего пользователя в виде статичной таблицы
            if user_tuples:
                st.write(f"**Отношения пользователя {user_id}:**")
                
                # Создаем данные для таблицы
                relation_data = []
                for tuple_data in user_tuples:
                    entity = tuple_data.get("entity", {})
                    subject = tuple_data.get("subject", {})
                    relation = tuple_data.get("relation", "")
                    
                    relation_data.append({
                        "Тип сущности": entity.get("type", ""),
                        "ID сущности": entity.get("id", ""),
                        "Отношение": relation,
                        "Тип субъекта": subject.get("type", ""),
                        "ID субъекта": subject.get("id", ""),
                        "Полное отношение": f"{entity.get('type')}:{entity.get('id')} → {relation} → {subject.get('type')}:{subject.get('id')}"
                    })
                
                # Создаем DataFrame для отображения таблицы
                df = pd.DataFrame(relation_data)
                
                # Отображаем статичную таблицу
                st.dataframe(df, use_container_width=True)
            
            # Показываем остальные отношения
            other_tuples = [t for t in tuples if t not in user_tuples]
            if other_tuples:
                st.write("**Другие отношения:**")
                for tuple_data in other_tuples[:5]:  # Показываем только первые 5
                    entity = tuple_data.get("entity", {})
                    subject = tuple_data.get("subject", {})
                    relation = tuple_data.get("relation", "")
                    st.write(f"{entity.get('type')}:{entity.get('id')} → {relation} → {subject.get('type')}:{subject.get('id')}")
                if len(other_tuples) > 5:
                    st.write(f"...и еще {len(other_tuples) - 5} отношений")
        except Exception as e:
            st.warning(f"Не удалось показать отношения: {str(e)}")
    
    if st.button("Проверить доступ", type="primary"):
        success, result = check_permission(entity_type, entity_id, permission, user_id, tenant_id, selected_schema_version)
        
        if success:
            # Правильно интерпретируем результат
            can_access = False
            
            # Проверяем, что result - это словарь
            if isinstance(result, dict) and "can" in result:
                # Проверяем в зависимости от того, как возвращается результат
                if isinstance(result["can"], bool):
                    can_access = result["can"]
                elif result["can"] == "CHECK_RESULT_ALLOWED":
                    can_access = True
                
                if can_access:
                    st.success(f"✅ Доступ разрешен: пользователь {user_id} имеет разрешение {permission} для {entity_type}:{entity_id}")
                    
                    # Показываем подробную информацию о решении, если она есть
                    if "metadata" in result:
                        with st.expander("Подробная информация о решении"):
                            st.json(result["metadata"])
                    
                    # Предупреждение о возможной проблеме с wildcard
                    if entity_id == "*" and can_access:
                        st.warning("⚠️ Внимание: Вы используете wildcard '*' в ID сущности. Это может давать неожиданные разрешения.")
                else:
                    st.error(f"❌ Доступ запрещен: пользователь {user_id} не имеет разрешения {permission} для {entity_type}:{entity_id}")
                
                # Всегда показываем полный ответ для отладки
                with st.expander("Детали ответа API"):
                    st.json(result)
            else:
                # Если result не словарь или не содержит ключ "can"
                st.error("Ошибка в формате ответа API")
                st.json(result)
        else:
            # В случае ошибки показываем сообщение
            st.error(result)
            
            # Добавляем рекомендацию по исправлению, если схема не найдена
            if isinstance(result, str) and "ERROR_CODE_SCHEMA_NOT_FOUND" in result:
                st.warning("""
                **Схема не найдена!**
                
                Возможные причины:
                1. Схема еще не загружена в Permify
                2. Указана неверная версия схемы
                
                Рекомендации:
                - Перейдите в раздел "Схемы" и загрузите схему из файла schema.perm
                - Убедитесь, что сущность и разрешение указаны правильно
                """)

# Информация о системе
elif menu == "Статус системы":
    st.header("Статус системы")
    
    # Информация о Permify
    st.subheader("Информация о Permify")
    
    # Проверяем статус
    status, message = check_permify_status()
    if status:
        st.success(f"✅ Permify доступен: {message}")
    else:
        st.error(f"❌ Permify недоступен: {message}")
    
    # Информация о подключении
    st.write(f"**REST API URL:** {PERMIFY_HOST}")
    st.write(f"**gRPC API URL:** {PERMIFY_GRPC_HOST}")
    st.write(f"**Арендатор по умолчанию:** {DEFAULT_TENANT}")
    
    # Проверка статуса портов
    st.subheader("Проверка API портов")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Проверить REST API"):
            try:
                response = requests.get(f"{PERMIFY_HOST}/healthz")
                st.code(f"Статус: {response.status_code}\nОтвет: {response.text}")
            except Exception as e:
                st.error(f"Ошибка соединения: {str(e)}")
    
    with col2:
        if st.button("Проверить gRPC API"):
            try:
                import socket
                host, port = PERMIFY_GRPC_HOST.replace("http://", "").replace("https://", "").split(":")
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                result = sock.connect_ex((host, int(port)))
                if result == 0:
                    st.success(f"✅ Порт {port} открыт")
                else:
                    st.error(f"❌ Порт {port} закрыт")
                sock.close()
            except Exception as e:
                st.error(f"Ошибка проверки порта: {str(e)}")

# Информация в футере
st.markdown("---")
st.markdown("### О приложении")
st.markdown("Это приложение позволяет управлять схемами и отношениями в системе авторизации Permify.") 