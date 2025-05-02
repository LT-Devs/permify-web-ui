import streamlit as st
import pandas as pd
import os
from pathlib import Path
from .base_view import BaseView
from app.controllers import SchemaController

class SchemaView(BaseView):
    """Представление для управления схемами в ручном режиме."""
    
    def __init__(self):
        super().__init__()
        self.controller = SchemaController()
    
    def server_file_selector(self, folder_path='.', extensions=None):
        """Выбор файлов на сервере."""
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
    
    def load_schema_from_file(self, file_path):
        """Загружает схему из файла."""
        try:
            with open(file_path, 'r') as f:
                schema_content = f.read()
            return schema_content
        except Exception as e:
            st.error(f"Ошибка при чтении файла: {str(e)}")
            return None
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс управления схемами."""
        self.show_header("Управление схемами", "Создание и редактирование схем Permify")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("schema_view")
        
        # Показываем все версии схем
        st.subheader("Версии схем")
        
        if st.button("Получить все версии схем"):
            try:
                # Получаем список всех схем
                success, schemas_result = self.controller.get_schema_list(tenant_id)
                if not success:
                    st.error(f"Ошибка получения списка схем: {schemas_result}")
                else:
                    schemas_list = schemas_result
                    
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
                                        success, schema_result = self.controller.get_current_schema(tenant_id, schema_version)
                                        
                                        if success:
                                            st.json(schema_result)
                                            
                                            # Если есть данные о схеме, попробуем отобразить их в более читаемом виде
                                            if 'schema' in schema_result:
                                                st.subheader("Содержимое схемы:")
                                                if 'entityDefinitions' in schema_result['schema']:
                                                    entities = schema_result['schema']['entityDefinitions']
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
                                            st.error(f"Ошибка при получении схемы {schema_version}: {schema_result}")
                                    except Exception as e:
                                        st.error(f"Ошибка при просмотре схемы: {str(e)}")
            except Exception as e:
                st.error(f"Ошибка: {str(e)}")
        
        # Показываем текущую (последнюю) схему
        st.subheader("Текущая схема")
        if st.button("Получить текущую схему"):
            success, result = self.controller.get_current_schema(tenant_id)
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
                is_valid, validation_msg = self.controller.validate_schema(schema_content)
                if is_valid:
                    st.success("✅ Схема валидна")
                    if st.button("Создать схему в Permify"):
                        success, message = self.controller.create_schema(schema_content, tenant_id)
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                else:
                    st.error(f"❌ {validation_msg}")
        
        elif upload_type == "Выбрать файл на сервере":
            # Опция выбора директории
            base_dir = st.text_input("Базовая директория", value=".")
            schema_file = self.server_file_selector(base_dir, extensions=["perm"])
            
            if schema_file:
                schema_content = self.load_schema_from_file(schema_file)
                if schema_content:
                    st.code(schema_content, language="perm")
                    
                    # Валидация схемы
                    is_valid, validation_msg = self.controller.validate_schema(schema_content)
                    if is_valid:
                        st.success("✅ Схема валидна")
                        if st.button("Создать схему в Permify"):
                            success, message = self.controller.create_schema(schema_content, tenant_id)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                    else:
                        st.error(f"❌ {validation_msg}")
        
        elif upload_type == "Ввести схему вручную":
            manual_schema = st.text_area("Введите схему вручную", height=300)
            
            if manual_schema:
                # Кнопка для валидации схемы
                if st.button("Валидировать схему"):
                    is_valid, validation_msg = self.controller.validate_schema(manual_schema)
                    if is_valid:
                        st.success("✅ Схема валидна")
                    else:
                        st.error(f"❌ {validation_msg}")
            
                if st.button("Создать схему из текста"):
                    if manual_schema:
                        # Сначала валидируем
                        is_valid, validation_msg = self.controller.validate_schema(manual_schema)
                        if is_valid:
                            success, message = self.controller.create_schema(manual_schema, tenant_id)
                            if success:
                                st.success(message)
                            else:
                                st.error(message)
                        else:
                            st.error(f"❌ {validation_msg}")
                    else:
                        st.warning("Введите схему перед созданием") 