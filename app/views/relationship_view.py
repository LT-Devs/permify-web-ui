import streamlit as st
import pandas as pd
from .base_view import BaseView
from app.controllers import RelationshipController, AppController, UserController, GroupController
from .styles import get_dark_mode_styles

class RelationshipView(BaseView):
    """Представление для управления отношениями между объектами в Permify."""
    
    def __init__(self):
        super().__init__()
        self.relationship_controller = RelationshipController()
        self.app_controller = AppController()
        self.user_controller = UserController()
        self.group_controller = GroupController()
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс управления отношениями."""
        self.show_header("Управление отношениями", 
                         "Создание и редактирование отношений между объектами")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("relationship_view")
        
        # Получаем данные
        success, relationships = self.relationship_controller.get_relationships(tenant_id)
        apps = self.app_controller.get_apps(tenant_id)
        users = self.user_controller.get_users(tenant_id)
        groups = self.group_controller.get_groups(tenant_id)
        
        # Добавляем стили для улучшения визуального представления
        st.markdown(get_dark_mode_styles(), unsafe_allow_html=True)
        
        st.subheader("Текущие отношения в системе")
        
        if success and relationships:
            tuples = relationships.get("tuples", [])
            
            if tuples:
                # Фильтры для отношений
                col1, col2 = st.columns(2)
                with col1:
                    entity_filter = st.text_input("Фильтр по типу сущности", key="entity_filter")
                with col2:
                    subject_filter = st.text_input("Фильтр по типу субъекта", key="subject_filter")
                
                # Фильтруем отношения
                filtered_tuples = tuples
                if entity_filter:
                    filtered_tuples = [t for t in filtered_tuples 
                                      if entity_filter.lower() in t.get("entity", {}).get("type", "").lower()]
                if subject_filter:
                    filtered_tuples = [t for t in filtered_tuples 
                                      if subject_filter.lower() in t.get("subject", {}).get("type", "").lower()]
                
                # Создаем данные для таблицы
                relation_data = []
                for tuple_data in filtered_tuples:
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
                if relation_data:
                    df = pd.DataFrame(relation_data)
                    st.dataframe(df, use_container_width=True)
                else:
                    st.info("Нет отношений, соответствующих фильтрам")
                
                # Интерфейс для создания нового отношения
                st.subheader("Создать новое отношение")
                
                col1, col2 = st.columns(2)
                with col1:
                    entity_type = st.selectbox(
                        "Тип сущности", 
                        sorted(list(set([app.get('name') for app in apps if app.get('name')]))),
                        key="new_rel_entity_type"
                    )
                    
                    entity_id = st.text_input(
                        "ID сущности", 
                        key="new_rel_entity_id",
                        help="Идентификатор сущности, например, '1'"
                    )
                    
                    relation_type = st.selectbox(
                        "Тип отношения", 
                        ["owner", "editor", "viewer", "member", "custom"],
                        key="new_rel_relation_type"
                    )
                    
                    if relation_type == "custom":
                        relation_custom = st.text_input(
                            "Название отношения", 
                            key="new_rel_relation_custom"
                        )
                
                with col2:
                    subject_type = st.selectbox(
                        "Тип субъекта", 
                        ["user", "group"],
                        key="new_rel_subject_type"
                    )
                    
                    if subject_type == "user":
                        subject_id = st.selectbox(
                            "ID пользователя", 
                            [user.get('id') for user in users],
                            format_func=lambda x: next((user.get('name', f"Пользователь {user.get('id')}") 
                                                      for user in users if user.get('id') == x), x),
                            key="new_rel_user_id"
                        )
                    else:
                        subject_id = st.selectbox(
                            "ID группы", 
                            [group.get('id') for group in groups],
                            format_func=lambda x: next((group.get('name', f"Группа {group.get('id')}") 
                                                      for group in groups if group.get('id') == x), x),
                            key="new_rel_group_id"
                        )
                
                # Кнопка для создания отношения
                if st.button("Создать отношение", key="create_relation_btn", type="primary"):
                    # Получаем фактическое отношение
                    actual_relation = relation_custom if relation_type == "custom" else relation_type
                    
                    if not entity_type or not entity_id or not actual_relation or not subject_id:
                        st.error("Заполните все поля для создания отношения")
                    else:
                        success, result = self.relationship_controller.create_relationship(
                            entity_type, entity_id, actual_relation, subject_type, subject_id, tenant_id
                        )
                        
                        if success:
                            st.success(f"Отношение успешно создано: {entity_type}:{entity_id} → {actual_relation} → {subject_type}:{subject_id}")
                            st.rerun()
                        else:
                            st.error(f"Ошибка создания отношения: {result}")
                
                # Интерфейс для удаления отношения
                st.subheader("Удалить отношение")
                
                if relation_data:
                    selected_relation_index = st.selectbox(
                        "Выберите отношение для удаления",
                        range(len(relation_data)),
                        format_func=lambda i: relation_data[i]["Полное отношение"],
                        key="relation_to_delete"
                    )
                    
                    selected_relation = relation_data[selected_relation_index]
                    
                    # Кнопка для удаления отношения
                    if st.button("Удалить отношение", key="delete_relation_btn"):
                        entity_type = selected_relation["Тип сущности"]
                        entity_id = selected_relation["ID сущности"]
                        relation = selected_relation["Отношение"]
                        subject_type = selected_relation["Тип субъекта"]
                        subject_id = selected_relation["ID субъекта"]
                        
                        success, result = self.relationship_controller.delete_relationship(
                            entity_type, entity_id, relation, subject_type, subject_id, tenant_id
                        )
                        
                        if success:
                            st.success(f"Отношение успешно удалено")
                            st.rerun()
                        else:
                            st.error(f"Ошибка удаления отношения: {result}")
            else:
                st.info("В системе нет отношений. Создайте новое отношение ниже.")
                
                # Интерфейс для создания первого отношения
                st.subheader("Создать первое отношение")
                
                col1, col2 = st.columns(2)
                with col1:
                    entity_type = st.selectbox(
                        "Тип сущности", 
                        sorted(list(set([app.get('name') for app in apps if app.get('name')]))),
                        key="first_entity_type"
                    )
                    
                    entity_id = st.text_input(
                        "ID сущности", 
                        key="first_entity_id",
                        help="Идентификатор сущности, например, '1'"
                    )
                    
                    relation_type = st.selectbox(
                        "Тип отношения", 
                        ["owner", "editor", "viewer", "member", "custom"],
                        key="first_relation_type"
                    )
                    
                    if relation_type == "custom":
                        relation_custom = st.text_input(
                            "Название отношения", 
                            key="first_relation_custom"
                        )
                
                with col2:
                    subject_type = st.selectbox(
                        "Тип субъекта", 
                        ["user", "group"],
                        key="first_subject_type"
                    )
                    
                    if subject_type == "user":
                        subject_id = st.selectbox(
                            "ID пользователя", 
                            [user.get('id') for user in users],
                            format_func=lambda x: next((user.get('name', f"Пользователь {user.get('id')}") 
                                                      for user in users if user.get('id') == x), x),
                            key="first_user_id"
                        )
                    else:
                        subject_id = st.selectbox(
                            "ID группы", 
                            [group.get('id') for group in groups],
                            format_func=lambda x: next((group.get('name', f"Группа {group.get('id')}") 
                                                      for group in groups if group.get('id') == x), x),
                            key="first_group_id"
                        )
                
                # Кнопка для создания отношения
                if st.button("Создать отношение", key="create_first_relation_btn", type="primary"):
                    # Получаем фактическое отношение
                    actual_relation = relation_custom if relation_type == "custom" else relation_type
                    
                    if not entity_type or not entity_id or not actual_relation or not subject_id:
                        st.error("Заполните все поля для создания отношения")
                    else:
                        success, result = self.relationship_controller.create_relationship(
                            entity_type, entity_id, actual_relation, subject_type, subject_id, tenant_id
                        )
                        
                        if success:
                            st.success(f"Отношение успешно создано: {entity_type}:{entity_id} → {actual_relation} → {subject_type}:{subject_id}")
                            st.rerun()
                        else:
                            st.error(f"Ошибка создания отношения: {result}")
        else:
            st.error("Не удалось получить отношения. Проверьте подключение к Permify.") 