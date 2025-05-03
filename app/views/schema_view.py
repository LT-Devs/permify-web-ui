import streamlit as st
import pandas as pd
import os
from pathlib import Path
from .base_view import BaseView
from app.controllers import SchemaController, AppController

class SchemaView(BaseView):
    """Представление для управления схемами в ручном режиме."""
    
    def __init__(self):
        super().__init__()
        self.controller = SchemaController()
        self.app_controller = AppController()
    
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
        
        tabs = st.tabs(["Текущая схема", "Создание схемы", "Версии схем", "Обновление схемы"])
        
        with tabs[0]:
            self.show_current_schema(tenant_id)
        
        with tabs[1]:
            self.show_schema_editor(tenant_id)
        
        with tabs[2]:
            self.show_schema_versions(tenant_id)
            
        with tabs[3]:
            self.show_schema_update_tools(tenant_id)
            
    def show_schema_update_tools(self, tenant_id: str):
        """Отображает инструменты для обновления схемы."""
        st.subheader("Инструменты обновления схемы")
        
        st.info("Данный раздел позволяет принудительно обновить схему на основе имеющихся данных об объектах, ролях и разрешениях.")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info("При нажатии на кнопку будет сгенерирована новая схема на основе всех имеющихся данных о приложениях, ролях и разрешениях.")
        
        with col2:
            if st.button("🔄 Пересоздать схему", type="primary", key="rebuild_schema_button"):
                with st.spinner("Обновление схемы..."):
                    success, result = self.app_controller.force_rebuild_schema(tenant_id)
                                        
                    if success:
                        st.success("✅ Схема успешно обновлена!")
                    else:
                        st.error(f"❌ Ошибка при обновлении схемы: {result}")
    
    def show_current_schema(self, tenant_id: str):
        """Отображает текущую схему."""
        st.subheader("Текущая схема")
        
        success, schema_result = self.controller.get_current_schema(tenant_id)
        
        if success:
            st.info(f"Версия схемы: {schema_result.get('version', 'Неизвестно')}")
            
            if "schema_string" in schema_result:
                st.code(schema_result["schema_string"], language="perm")
            else:
                st.json(schema_result)
        else:
            st.error(f"Ошибка получения схемы: {schema_result}")
    
    def show_schema_editor(self, tenant_id: str):
        """Отображает редактор схемы."""
        st.subheader("Создание новой схемы")
        
        # Загружаем текущую схему как образец
        success, schema_result = self.controller.get_current_schema(tenant_id)
        
        if success and "schema_string" in schema_result:
            default_schema = schema_result["schema_string"]
        else:
            default_schema = """entity user {}

entity group {
  relation member @user
}

entity document {
  relation owner @user
  relation editor @user
  relation viewer @user
  relation member @group
  
  action view = owner or editor or viewer or member
  action edit = owner or editor
  action delete = owner
}
"""
        
        schema_content = st.text_area("Содержимое схемы", 
                                    value=default_schema, 
                                    height=400,
                                    key="schema_editor")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("Проверить схему", key="validate_schema_button"):
                with st.spinner("Проверка схемы..."):
                    success, result = self.controller.validate_schema(schema_content)
                    
                    if success:
                        st.success("✅ Схема валидна")
                    else:
                        st.error(f"❌ Ошибка в схеме: {result}")
        
        with col2:
            if st.button("Создать схему", key="create_schema_button", type="primary"):
                with st.spinner("Создание схемы..."):
                    success, result = self.controller.create_schema(schema_content, tenant_id)
                    
                    if success:
                        st.success("✅ Схема успешно создана")
                    else:
                        st.error(f"❌ Ошибка при создании схемы: {result}")
    
    def show_schema_versions(self, tenant_id: str):
        """Отображает список версий схем."""
        st.subheader("Версии схем")
        
        success, schema_result = self.controller.get_schema_list(tenant_id)
        
        if success:
            schemas = schema_result.get("schemas", [])
            
            if not schemas:
                st.info("Нет доступных схем")
                return
            
            # Сортируем схемы по дате создания (новые сначала)
            sorted_schemas = sorted(schemas, key=lambda x: x.get('created_at', ''), reverse=True)
            
            # Создаем DataFrame для отображения
            schemas_data = []
            for schema in sorted_schemas:
                schemas_data.append({
                    "Версия": schema.get("version", ""),
                    "Дата создания": schema.get("created_at", "")
                })
            
            st.dataframe(
                pd.DataFrame(schemas_data),
                use_container_width=True,
                hide_index=True
            )
            
            # Выбор версии для просмотра
            versions = [schema.get("version") for schema in sorted_schemas]
            selected_version = st.selectbox(
                "Выберите версию для просмотра",
                versions,
                key="select_schema_version"
            )
            
            if selected_version:
                success, schema_result = self.controller.get_current_schema(tenant_id, selected_version)
                
                if success and "schema_string" in schema_result:
                    st.subheader(f"Схема версии {selected_version}")
                    st.code(schema_result["schema_string"], language="perm")
                elif success:
                    st.json(schema_result)
                else:
                    st.error(f"Ошибка получения схемы: {schema_result}")
            else:
                st.error(f"Ошибка получения списка схем: {schema_result}") 