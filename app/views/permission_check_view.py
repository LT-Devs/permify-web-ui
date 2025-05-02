import streamlit as st
import pandas as pd
from .base_view import BaseView
from app.controllers import RelationshipController, SchemaController

class PermissionCheckView(BaseView):
    """Представление для проверки разрешений в ручном режиме."""
    
    def __init__(self):
        super().__init__()
        self.controller = RelationshipController()
        self.schema_controller = SchemaController()
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс проверки разрешений."""
        self.show_header("Проверка доступа", "Проверка разрешений на действия над сущностями")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("permission_check_view")
        
        # Получаем список доступных схем
        success, schemas_result = self.schema_controller.get_schema_list(tenant_id)
        
        # Переменная для хранения выбранной версии схемы
        selected_schema_version = None
        
        if success:
            schemas_list = schemas_result
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
        success, schema_result = self.schema_controller.get_current_schema(tenant_id, selected_schema_version)
        
        # Информация о текущей схеме
        if success and isinstance(schema_result, dict):
            st.success(f"Загружена схема версии: {schema_result.get('version')}")
        
        # Получаем все отношения
        rel_success, rel_result = self.controller.get_relationships(tenant_id)
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Если схема успешно получена, предлагаем выбор из доступных в схеме типов
            if success and isinstance(schema_result, dict) and "schema" in schema_result:
                try:
                    entity_types = list(schema_result["schema"].get("entityDefinitions", {}).keys())
                    if entity_types:
                        entity_type = st.selectbox("Тип сущности", entity_types, index=entity_types.index("petitions") if "petitions" in entity_types else 0)
                    else:
                        entity_type = st.text_input("Тип сущности", "petitions", key="perm_check_entity_type_input")
                except Exception as e:
                    st.warning(f"Не удалось получить типы сущностей из схемы: {str(e)}")
                    entity_type = st.text_input("Тип сущности", "petitions", key="perm_check_entity_type_fallback")
            else:
                entity_type = st.text_input("Тип сущности", "petitions", key="perm_check_entity_type_manual")
            
            entity_id = st.text_input("ID сущности", "1", key="perm_check_entity_id")
            
            # Если схема успешно получена, предлагаем выбор из доступных в схеме разрешений
            if success and isinstance(schema_result, dict) and "schema" in schema_result:
                try:
                    entity_def = schema_result["schema"].get("entityDefinitions", {}).get(entity_type, {})
                    permissions = list(entity_def.get("permissions", {}).keys())
                    if permissions:
                        permission = st.selectbox("Разрешение", permissions, key="perm_check_permission_select")
                    else:
                        permission = st.text_input("Разрешение", "read", key="perm_check_permission_input")
                except Exception as e:
                    st.warning(f"Не удалось получить разрешения из схемы: {str(e)}")
                    permission = st.text_input("Разрешение", "read", key="perm_check_permission_fallback")
            else:
                permission = st.text_input("Разрешение", "read", key="perm_check_permission_manual")
        
        with col2:
            user_id = st.text_input("ID пользователя", "1", key="perm_check_user_id")
        
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
            success, result = self.controller.check_permission(entity_type, entity_id, permission, user_id, tenant_id, selected_schema_version)
            
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