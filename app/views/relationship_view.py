import streamlit as st
import pandas as pd
from .base_view import BaseView
from app.controllers import RelationshipController

class RelationshipView(BaseView):
    """Представление для управления отношениями в ручном режиме."""
    
    def __init__(self):
        super().__init__()
        self.controller = RelationshipController()
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс управления отношениями."""
        self.show_header("Управление отношениями", "Создание и редактирование отношений между сущностями")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("relationship_view")
        
        # Показываем текущие отношения
        st.subheader("Текущие отношения")
        
        # Создаем контейнер для отображения сообщений об удалении
        delete_message_container = st.empty()
        
        # Хранение состояния для выбранных отношений
        if 'selected_relations' not in st.session_state:
            st.session_state.selected_relations = []
        
        # Получаем все отношения при открытии страницы или при нажатии кнопки
        if st.button("Обновить отношения") or 'relationships_loaded' not in st.session_state:
            success, result = self.controller.get_relationships(tenant_id)
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
                            success_count, error_count, errors = self.controller.delete_multiple_relationships(selected_rows, tenant_id)
                            
                            if success_count > 0:
                                delete_message_container.success(f"Успешно удалено отношений: {success_count}")
                                # Перезагружаем данные
                                success, result = self.controller.get_relationships(tenant_id)
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
            success, message = self.controller.create_relationship(
                new_entity_type, new_entity_id, new_relation, new_subject_type, new_subject_id, tenant_id
            )
            if success:
                st.success(f"Отношение успешно создано: {message}")
                # Обновляем данные
                success, result = self.controller.get_relationships(tenant_id)
                if success:
                    st.session_state.relationship_result = result
                    st.rerun()  # Перезагружаем страницу для обновления списка
            else:
                st.error(message) 