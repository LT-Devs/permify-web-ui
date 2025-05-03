import streamlit as st
import pandas as pd
from .base_view import BaseView
from app.controllers import AppController, UserController, GroupController
from .styles import get_dark_mode_styles

class AppView(BaseView):
    """Представление для управления приложениями в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.controller = AppController()
        self.user_controller = UserController()
        self.group_controller = GroupController()
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс управления приложениями."""
        self.show_header("Управление приложениями", 
                         "Создание и редактирование приложений, настройка действий и прав доступа")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("app_view")
        
        # Получаем данные
        apps = self.controller.get_apps(tenant_id)
        users = self.user_controller.get_users(tenant_id)
        groups = self.group_controller.get_groups(tenant_id)
        
        # Разделяем приложения на шаблоны и экземпляры
        templates = [app for app in apps if app.get('is_template', False)]
        instances = [app for app in apps if not app.get('is_template', False)]
        
        # Создание нового приложения
        with st.container():
            st.subheader("Создать новый объект")
            
            # Добавляем информационное сообщение
            st.info("""
            **Как создать новый объект:**
            1. Укажите название объекта (например, "orders", "documents", "projects")
            2. Введите ID объекта (например, "1", "main")
            3. Настройте действия, которые можно выполнять с объектом
            4. Укажите, какие роли могут выполнять каждое действие
            """)
            
            # Добавляем стили для улучшения контрастности
            st.markdown(get_dark_mode_styles(), unsafe_allow_html=True)
            
            # Проверяем, нужно ли сбросить форму
            if 'reset_app_form' in st.session_state and st.session_state.reset_app_form:
                if 'app_actions' in st.session_state:
                    st.session_state.app_actions = [
                        {"name": "view", "editor_allowed": True, "viewer_allowed": True, "group_allowed": True},
                        {"name": "edit", "editor_allowed": True, "viewer_allowed": False, "group_allowed": False},
                        {"name": "delete", "editor_allowed": False, "viewer_allowed": False, "group_allowed": False}
                    ]
                # Сбрасываем флаг сброса формы
                st.session_state.reset_app_form = False
            
            col1, col2 = st.columns(2)
            with col1:
                new_app_name = st.text_input(
                    "Название объекта (без пробелов, латиницей)",
                    key="new_app_name",
                    help="Используйте только латинские буквы и цифры, без пробелов и специальных символов"
                )
            with col2:
                new_app_id = st.text_input(
                    "ID объекта", 
                    "1", 
                    key="new_app_id",
                    help="Идентификатор объекта (например, '1' для основного экземпляра)"
                )
            
            # Добавление действий для объекта
            st.markdown("### Настройка действий (permissions)")
            st.caption("Укажите, какие действия можно выполнять с этим объектом и кто имеет на них право")
            
            if 'app_actions' not in st.session_state:
                st.session_state.app_actions = [
                    {"name": "view", "editor_allowed": True, "viewer_allowed": True, "group_allowed": True},
                    {"name": "edit", "editor_allowed": True, "viewer_allowed": False, "group_allowed": False},
                    {"name": "delete", "editor_allowed": False, "viewer_allowed": False, "group_allowed": False}
                ]
            
            # Добавляем поддержку настраиваемых отношений
            if 'custom_relations' not in st.session_state:
                st.session_state.custom_relations = []
            
            # Инициализируем пользовательские отношения из базы данных при первом запуске
            if not st.session_state.custom_relations:
                custom_relations = self.controller.get_all_custom_relations()
                st.session_state.custom_relations = custom_relations
                
                # Принудительно сохраняем пользовательские отношения в файл
                if custom_relations:
                    print(f"Принудительное сохранение пользовательских отношений: {custom_relations}")
                    # Получаем все приложения
                    apps = self.controller.get_apps(tenant_id)
                    # Обновляем метаданные в каждом приложении
                    for app in apps:
                        # Сохраняем отношения в метаданных
                        if 'metadata' not in app:
                            app['metadata'] = {}
                        if 'custom_relations' not in app['metadata']:
                            app['metadata']['custom_relations'] = []
                        
                        # Добавляем все кастомные отношения
                        for relation in custom_relations:
                            if relation not in app['metadata']['custom_relations']:
                                app['metadata']['custom_relations'].append(relation)
                        
                        # Обновляем приложение
                        if 'actions' in app:
                            self.controller.update_app(
                                app['name'], app['id'], app['actions'], tenant_id, 
                                metadata=app['metadata']
                            )
            
            # Получаем ранее сохраненные отношения для обновления списка
            all_apps = self.controller.get_apps(tenant_id)
            for app in all_apps:
                if 'metadata' in app and 'custom_relations' in app.get('metadata', {}):
                    for relation in app.get('metadata', {}).get('custom_relations', []):
                        if relation not in st.session_state.custom_relations:
                            st.session_state.custom_relations.append(relation)
            
            # Создаем карточку для создания отношения
            with st.container():
                st.markdown("""
                <style>
                .relation-card {
                    background-color: #1e2025;
                    border: 1px solid #4e5259;
                    border-radius: 5px;
                    padding: 15px;
                    margin-bottom: 15px;
                }
                .relation-pill {
                    display: inline-block;
                    background-color: #2d3035;
                    color: #e0e0e0;
                    border-radius: 15px;
                    padding: 5px 12px;
                    margin: 5px;
                    font-size: 14px;
                }
                .relation-pill-container {
                    margin-top: 10px;
                    margin-bottom: 10px;
                }
                .custom-header {
                    background-color: #333740;
                    padding: 10px 15px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                    color: #e0e0e0;
                    font-weight: bold;
                }
                .action-table {
                    margin-top: 15px;
                    margin-bottom: 15px;
                }
                .relation-header {
                    background-color: #333740;
                    padding: 10px 15px;
                    border-radius: 5px;
                    margin-bottom: 15px;
                    color: #e0e0e0;
                    font-weight: bold;
                }
                </style>
                """, unsafe_allow_html=True)
                
                st.markdown("<div class='custom-header'>Настраиваемые типы отношений</div>", unsafe_allow_html=True)
                
                # Форма добавления кастомного отношения с улучшенным дизайном
                st.markdown("<div class='relation-card'>", unsafe_allow_html=True)
                st.markdown("**Добавить новый тип отношения**", unsafe_allow_html=True)
                st.caption("Здесь вы можете создать собственный тип отношения, который можно использовать в разделе 'Отношения'")
                
                col1, col2 = st.columns([3, 1])
                with col1:
                    new_relation = st.text_input(
                        "Название типа отношения", 
                        placeholder="Например: reviewer, approver, manager",
                        key="new_custom_relation"
                    )
                with col2:
                    st.write("")
                    st.write("")
                    if st.button("➕ Добавить", key="add_custom_relation", type="primary"):
                        if new_relation.strip():
                            if new_relation not in st.session_state.custom_relations and new_relation.isalnum():
                                st.session_state.custom_relations.append(new_relation)
                                st.success(f"Тип отношения '{new_relation}' добавлен")
                                st.rerun()
                            elif not new_relation.isalnum():
                                st.error("Название должно содержать только буквы и цифры без пробелов")
                            else:
                                st.warning(f"Тип отношения '{new_relation}' уже существует")
                        else:
                            st.warning("Введите название типа отношения")
                st.markdown("</div>", unsafe_allow_html=True)
                
                # Отображаем добавленные типы отношений в виде плиток
                if st.session_state.custom_relations:
                    st.markdown("<div class='relation-card'>", unsafe_allow_html=True)
                    st.markdown("**Добавленные типы отношений**", unsafe_allow_html=True)
                    st.markdown("<div class='relation-pill-container'>", unsafe_allow_html=True)
                    
                    relation_columns = st.columns(4)
                    for i, relation in enumerate(st.session_state.custom_relations):
                        col_idx = i % 4
                        with relation_columns[col_idx]:
                            cols = st.columns([3, 1])
                            with cols[0]:
                                st.markdown(f"<div class='relation-pill'>{relation}</div>", unsafe_allow_html=True)
                            with cols[1]:
                                if st.button("❌", key=f"remove_relation_{i}", help=f"Удалить тип отношения '{relation}'"):
                                    st.session_state.custom_relations.remove(relation)
                                    # Удаляем права из действий
                                    for action in st.session_state.app_actions:
                                        if f"{relation}_allowed" in action:
                                            del action[f"{relation}_allowed"]
                                    st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    st.markdown("</div>", unsafe_allow_html=True)
            
            # Настройка действий с улучшенным дизайном
            st.markdown("<div class='custom-header'>Настройка действий (permissions)</div>", unsafe_allow_html=True)
            st.caption("Укажите, какие действия можно выполнять с этим объектом и кто имеет на них право")
            
            # Заголовки для таблицы действий
            cols = st.columns([3, 2, 2, 2, 1])
            with cols[0]:
                st.markdown('<div class="perm-header">Действие</div>', unsafe_allow_html=True)
            with cols[1]:
                st.markdown('<div class="perm-header">Редакторы</div>', unsafe_allow_html=True)
            with cols[2]:
                st.markdown('<div class="perm-header">Просмотрщики</div>', unsafe_allow_html=True)
            with cols[3]:
                st.markdown('<div class="perm-header">Группы</div>', unsafe_allow_html=True)
            
            # Отображаем существующие действия
            for i, action in enumerate(st.session_state.app_actions):
                # Добавляем div с классом для стилизации строки
                st.markdown(f'<div class="action-row">', unsafe_allow_html=True)
                
                cols = st.columns([3, 2, 2, 2, 1])
                with cols[0]:
                    st.session_state.app_actions[i]["name"] = st.text_input(
                        label="Название действия",
                        value=action["name"], 
                        placeholder="Имя действия (например, view, edit, export)",
                        key=f"action_name_{i}",
                        label_visibility="collapsed"
                    )
                
                with cols[1]:
                    st.session_state.app_actions[i]["editor_allowed"] = st.checkbox(
                        "Редакторы", 
                        action["editor_allowed"],
                        key=f"editor_{i}",
                        help="Редакторы могут выполнять это действие"
                    )
                
                with cols[2]:
                    st.session_state.app_actions[i]["viewer_allowed"] = st.checkbox(
                        "Просмотрщики", 
                        action["viewer_allowed"],
                        key=f"viewer_{i}",
                        help="Просмотрщики могут выполнять это действие"
                    )
                
                with cols[3]:
                    st.session_state.app_actions[i]["group_allowed"] = st.checkbox(
                        "Группы", 
                        action["group_allowed"],
                        key=f"groups_{i}",
                        help="Группы могут выполнять это действие"
                    )
                
                with cols[4]:
                    if st.button("❌", key=f"remove_action_{i}", help="Удалить это действие"):
                        if len(st.session_state.app_actions) > 1:
                            st.session_state.app_actions.pop(i)
                            st.rerun()
            
                # Добавляем чекбоксы для пользовательских типов отношений
                if st.session_state.custom_relations:
                    with st.container():
                        st.markdown("<div class='relation-header'>Пользовательские типы отношений</div>", unsafe_allow_html=True)
                        st.markdown("<div style='margin-left: 10px; margin-top: 10px;'>", unsafe_allow_html=True)
                        
                        # Разделяем на колонки для более компактного отображения
                        custom_cols = st.columns(3)
                        for j, relation in enumerate(st.session_state.custom_relations):
                            col_index = j % 3
                            with custom_cols[col_index]:
                                relation_key = f"{relation}_allowed"
                                if relation_key not in st.session_state.app_actions[i]:
                                    st.session_state.app_actions[i][relation_key] = False
                                
                                st.session_state.app_actions[i][relation_key] = st.checkbox(
                                    relation, 
                                    st.session_state.app_actions[i].get(relation_key, False),
                                    key=f"{relation}_{i}",
                                    help=f"Пользователи с отношением '{relation}' могут выполнять это действие"
                                )
                        
                        st.markdown("</div>", unsafe_allow_html=True)
                
                # Закрываем div контейнера
                st.markdown('</div>', unsafe_allow_html=True)
            
            col1, col2 = st.columns([6, 4])
            with col1:
            # Кнопка для добавления нового действия
                if st.button("➕ Добавить действие", key="add_action"):
                    st.session_state.app_actions.append(
                        {"name": "", "editor_allowed": False, "viewer_allowed": False, "group_allowed": False}
                    )
                    st.rerun()
            
            with col2:
            # Кнопка для создания приложения
                if st.button("💾 Создать объект", key="create_app", type="primary"):
                    if new_app_name and new_app_id:
                        # Проверка на пустые или невалидные имена действий
                        valid_actions = [action for action in st.session_state.app_actions 
                                           if action["name"].strip()]

                        if not valid_actions:
                                st.error("Добавьте хотя бы одно действие и укажите его название")
                        else:
                                # Сохраняем пользовательские отношения вместе с приложением
                                metadata = {}
                                if st.session_state.custom_relations:
                                    metadata["custom_relations"] = st.session_state.custom_relations

                                # Копируем все пользовательские разрешения из действий
                                for action in valid_actions:
                                    custom_keys = [k for k in action.keys() if k.endswith("_allowed") 
                                                  and k not in ["editor_allowed", "viewer_allowed", "group_allowed"]]
                                    for key in custom_keys:
                                        relation = key.replace("_allowed", "")
                                        if relation not in metadata.get("custom_relations", []):
                                            if "custom_relations" not in metadata:
                                                metadata["custom_relations"] = []
                                            metadata["custom_relations"].append(relation)
                            
                                success, message = self.controller.create_app(
                                    new_app_name, new_app_id, valid_actions, tenant_id, metadata=metadata
                                )
                        
                        if success:
                            st.success(f"Объект {new_app_name} успешно сохранен")
                            # Устанавливаем флаг для сброса формы при следующей перезагрузке
                            st.session_state.reset_app_form = True
                            st.rerun()
                        else:
                            st.error(message)
                else:
                        st.warning("Введите название и ID объекта")
        
        # Обзор приложений
        if instances:
            st.markdown("---")
            st.subheader("Список объектов")
        
            # Создаем таблицу приложений для обзора
            app_data = []
            for app in instances:
                user_count = len(app.get('users', []))
                group_count = len(app.get('groups', []))
                action_count = len(app.get('actions', []))
                
                app_data.append({
                    "Название": app.get('display_name'),
                    "ID": app.get('id'),
                    "Тип": app.get('name'),
                    "Пользователей": user_count,
                    "Групп": group_count,
                    "Действий": action_count,
                    "_app_index": instances.index(app)  # Сохраняем индекс для редактирования
                })
            
            if app_data:
                # Скрываем служебное поле индекса
                display_df = pd.DataFrame(app_data).drop(columns=["_app_index"])
                st.dataframe(
                    display_df,
                    use_container_width=True,
                    hide_index=True
                )

                # Добавляем возможность редактирования объекта
                st.subheader("Редактировать объект")
                
                app_options = [(i, f"{app['display_name']} (ID: {app['id']})") for i, app in enumerate(instances)]
                selected_app_index = st.selectbox(
                    "Выберите объект для редактирования",
                    range(len(app_options)),
                    format_func=lambda i: app_options[i][1],
                    key="select_app_to_edit"
                )
                selected_app = instances[selected_app_index]
                
                with st.expander("Редактирование действий объекта", expanded=True):
                    # Инициализируем session_state для редактирования
                    if 'edit_app_actions' not in st.session_state or st.session_state.get('current_edit_app') != f"{selected_app['name']}:{selected_app['id']}":
                        st.session_state.edit_app_actions = []
                        for action in selected_app.get('actions', []):
                            # Создаем базовый словарь с основными разрешениями
                            action_data = {
                                "name": action.get('name', ''),
                                "editor_allowed": action.get('editor_allowed', False),
                                "viewer_allowed": action.get('viewer_allowed', False),
                                "group_allowed": action.get('group_allowed', False)
                            }
                            
                            # Добавляем пользовательские свойства
                            for key, value in action.items():
                                if key.endswith("_allowed") and key not in ["editor_allowed", "viewer_allowed", "group_allowed"]:
                                    action_data[key] = value
                            
                            st.session_state.edit_app_actions.append(action_data)
                        
                        st.session_state.current_edit_app = f"{selected_app['name']}:{selected_app['id']}"
                    
                    # Изменяем дизайн секции редактирования действий
                    st.markdown("<div class='custom-header'>Редактирование действий</div>", unsafe_allow_html=True)
                    st.caption("Изменение разрешений для этого объекта")
                    
                    # Проверяем и загружаем пользовательские отношения из метаданных
                    custom_relations_from_app = []
                    if 'metadata' in selected_app and 'custom_relations' in selected_app.get('metadata', {}):
                        custom_relations_from_app = selected_app.get('metadata', {}).get('custom_relations', [])
                        # Обновляем список кастомных отношений в сессии
                        for relation in custom_relations_from_app:
                            if relation not in st.session_state.custom_relations:
                                st.session_state.custom_relations.append(relation)
                    
                    # Отображаем существующие действия
                    for i, action in enumerate(st.session_state.edit_app_actions):
                        # Добавляем div с классом для стилизации строки
                        st.markdown(f'<div class="action-row">', unsafe_allow_html=True)
                        
                        cols = st.columns([3, 2, 2, 2, 1])
                        with cols[0]:
                            st.session_state.edit_app_actions[i]["name"] = st.text_input(
                                label="Название действия",
                                value=action["name"], 
                                placeholder="Имя действия (например, view, edit, export)",
                                key=f"edit_action_name_{i}",
                                label_visibility="collapsed"
                            )
                        
                        with cols[1]:
                            st.session_state.edit_app_actions[i]["editor_allowed"] = st.checkbox(
                                "Редакторы",
                                action["editor_allowed"],
                                key=f"edit_editor_{i}",
                                help="Редакторы могут выполнять это действие"
                            )
                        
                        with cols[2]:
                            st.session_state.edit_app_actions[i]["viewer_allowed"] = st.checkbox(
                                "Просмотрщики",
                                action["viewer_allowed"],
                                key=f"edit_viewer_{i}",
                                help="Просмотрщики могут выполнять это действие"
                            )
                        
                        with cols[3]:
                            st.session_state.edit_app_actions[i]["group_allowed"] = st.checkbox(
                                "Группы",
                                action["group_allowed"],
                                key=f"edit_groups_{i}",
                                help="Группы могут выполнять это действие"
                            )
                        
                        with cols[4]:
                            if st.button("❌", key=f"edit_remove_action_{i}", help="Удалить это действие"):
                                if len(st.session_state.edit_app_actions) > 1:
                                    st.session_state.edit_app_actions.pop(i)
                                    st.rerun()
                        
                        # Собираем все пользовательские отношения
                        all_custom_relations = list(st.session_state.custom_relations)
                        
                        # Добавляем отношения из действия
                        for key in action.keys():
                            if key.endswith("_allowed") and key not in ["editor_allowed", "viewer_allowed", "group_allowed"]:
                                relation = key.replace("_allowed", "")
                                if relation not in all_custom_relations:
                                    all_custom_relations.append(relation)
                        
                        # Добавляем чекбоксы для пользовательских типов отношений
                        if all_custom_relations:
                            with st.container():
                                st.markdown("<div class='relation-header'>Пользовательские типы отношений</div>", unsafe_allow_html=True)
                                st.markdown("<div style='margin-left: 10px; margin-top: 10px;'>", unsafe_allow_html=True)
                                
                                # Разделяем на колонки для более компактного отображения
                                custom_cols = st.columns(3)
                                for j, relation in enumerate(all_custom_relations):
                                    col_index = j % 3
                                    with custom_cols[col_index]:
                                        relation_key = f"{relation}_allowed"
                                        if relation_key not in st.session_state.edit_app_actions[i]:
                                            st.session_state.edit_app_actions[i][relation_key] = False
                                        
                                        st.session_state.edit_app_actions[i][relation_key] = st.checkbox(
                                            relation, 
                                            st.session_state.edit_app_actions[i].get(relation_key, False),
                                            key=f"edit_{relation}_{i}",
                                            help=f"Пользователи с отношением '{relation}' могут выполнять это действие"
                                        )
                                
                                st.markdown("</div>", unsafe_allow_html=True)
                        
                        # Закрываем div контейнера
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    col1, col2 = st.columns([6, 4])
                    with col1:
                        # Кнопка для добавления нового действия
                        if st.button("➕ Добавить действие", key="edit_add_action"):
                            st.session_state.edit_app_actions.append(
                                {"name": "", "editor_allowed": False, "viewer_allowed": False, "group_allowed": False}
                            )
                            st.rerun()
                    
                    with col2:
                        # Кнопка для сохранения изменений
                        if st.button("💾 Сохранить изменения", key="save_app_edits", type="primary"):
                            # Проверка на пустые или невалидные имена действий
                            valid_actions = [action for action in st.session_state.edit_app_actions 
                                           if action["name"].strip()]
                            
                            if not valid_actions:
                                st.error("Добавьте хотя бы одно действие и укажите его название")
                            else:
                                # Сохраняем пользовательские отношения вместе с приложением
                                metadata = {}
                                
                                # Собираем все пользовательские отношения
                                custom_relations = list(st.session_state.custom_relations)
                                
                                # Добавляем отношения из действий
                                for action in st.session_state.edit_app_actions:
                                    for key in action.keys():
                                        if key.endswith("_allowed") and key not in ["editor_allowed", "viewer_allowed", "group_allowed"]:
                                            relation = key.replace("_allowed", "")
                                            if relation not in custom_relations:
                                                custom_relations.append(relation)
                                
                                if custom_relations:
                                    metadata["custom_relations"] = custom_relations
                                
                                success, message = self.controller.update_app(
                                    selected_app['name'], selected_app['id'], valid_actions, tenant_id, metadata=metadata
                                )
                                
                                if success:
                                    st.success(f"Объект {selected_app['name']} успешно обновлен")
                                    st.rerun()
                                else:
                                    st.error(message)
        else:
            st.warning("Объекты не найдены. Создайте новый объект, используя форму выше.")
        
        # Управление приложениями
        if instances:
            st.markdown("---")
            st.subheader("Управление правами доступа")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Выбор приложения для управления
                app_options = [(i, f"{app['display_name']} (ID: {app['id']})") for i, app in enumerate(instances)]
                selected_app_index = st.selectbox(
                    "Выберите объект для настройки прав доступа",
                    range(len(app_options)),
                    format_func=lambda i: app_options[i][1],
                    key="select_app_to_manage"
                )
                selected_app = instances[selected_app_index]
            
            with col2:
                # Выбор вкладки для типа управления с более интуитивными иконками
                management_type = st.radio(
                    "Тип управления",
                    ["👤 Пользователи", "👥 Группы"],
                    horizontal=True,
                    key="management_type",
                    format_func=lambda x: x.split(" ")[1] if " " in x else x
                )
            
            # Управление пользователями
            if management_type == "👤 Пользователи":
                st.subheader(f"Управление пользователями для объекта: {selected_app['display_name']}")
                    
                # Информация о доступных действиях
                with st.expander("ℹ️ Действия с объектом", expanded=True):
                    actions_data = []
                    for action in selected_app.get('actions', []):
                        action_name = action.get('name', '')
                        editor_allowed = action.get('editor_allowed', False)
                        viewer_allowed = action.get('viewer_allowed', False)
                        group_allowed = action.get('group_allowed', False)
                        
                        allowed_roles = []
                        if True:  # Владельцы всегда имеют доступ
                            allowed_roles.append("Владельцы")
                        if editor_allowed:
                            allowed_roles.append("Редакторы")
                        if viewer_allowed:
                            allowed_roles.append("Просмотрщики")
                        if group_allowed:
                            allowed_roles.append("Группы")
                        
                        # Добавляем пользовательские отношения
                        for key, value in action.items():
                            if key.endswith("_allowed") and key not in ["editor_allowed", "viewer_allowed", "group_allowed"] and value:
                                relation = key.replace("_allowed", "")
                                allowed_roles.append(f"{relation}")
                        
                        actions_data.append({
                            "Действие": action_name,
                            "Доступно для": ", ".join(allowed_roles)
                        })
                    
                    if actions_data:
                        st.dataframe(
                            pd.DataFrame(actions_data),
                            use_container_width=True,
                            hide_index=True
                        )
                
                # Таблица текущих пользователей
                app_users = selected_app.get('users', [])
                if app_users:
                    st.markdown("#### Текущие пользователи объекта")
                    user_data = []
                    for user_role in app_users:
                        user_id = user_role.get('user_id')
                        role = user_role.get('role')
                        
                        # Находим имя пользователя
                        user_name = next((user.get('name', f"Пользователь {user.get('id')}") 
                                          for user in users if user.get('id') == user_id), 
                                         f"Пользователь {user_id}")
                        
                        # Переводим роль в удобочитаемый формат
                        standard_roles = {"owner": "Владелец", "editor": "Редактор", "viewer": "Просмотрщик"}
                        if role in standard_roles:
                            role_display = standard_roles[role]
                        else:
                            # Для пользовательских ролей используем капитализацию первой буквы
                            role_display = f"{role.capitalize()}"
                        
                        user_data.append({
                        "ID": user_id,
                            "Имя": user_name,
                            "Роль": role_display,
                            "_user_id": user_id,
                            "_role": role
                        })
                    
                    if user_data:
                        st.dataframe(
                            pd.DataFrame(user_data).drop(columns=["_user_id", "_role"]),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Удаление пользователя
                        with st.container():
                            st.markdown("#### Удалить пользователя")
                            col1, col2 = st.columns([3, 1])
                            with col1:
                                user_to_remove_index = st.selectbox(
                                    "Выберите пользователя для удаления",
                                    range(len(user_data)),
                                    format_func=lambda i: f"{user_data[i]['Имя']} ({user_data[i]['Роль']})",
                                    key="user_to_remove"
                                )
                            
                            with col2:
                                st.write(" ")
                                st.write(" ")
                                if st.button("❌ Удалить", key="remove_user_from_app"):
                                    user_id = user_data[user_to_remove_index]["_user_id"]
                                    role = user_data[user_to_remove_index]["_role"]
                                    
                                    success, message = self.controller.remove_user_from_app(
                                        selected_app.get('name'),
                                        selected_app.get('id'),
                                        user_id,
                                        role,
                                        tenant_id
                                    )
                                    if success:
                                        st.success(f"Пользователь удален из объекта")
                                        st.rerun()
                                    else:
                                        st.error(message)
                    else:
                        st.info("Нет пользователей с правами доступа к этому объекту")
                    
                # Добавление пользователя
                st.markdown("#### Добавить пользователя")
                
                available_users = [user for user in users]
                if available_users:
                    col1, col2, col3 = st.columns([2, 2, 1])
                    
                    with col1:
                            selected_user_index = st.selectbox(
                                "Выберите пользователя",
                            range(len(available_users)),
                            format_func=lambda i: f"{available_users[i].get('name', f'Пользователь {available_users[i].get('id')}')} (ID: {available_users[i].get('id')})",
                            key="user_to_add"
                            )
                    selected_user = available_users[selected_user_index]
                    
                    with col2:
                        role_options = [
                            ("owner", "👑 Владелец (полный доступ)"),
                            ("editor", "✏️ Редактор (может изменять)"),
                            ("viewer", "👁️ Просмотрщик (только чтение)")
                        ]
                        
                        # Добавляем пользовательские роли
                        custom_relations = []
                        if 'metadata' in selected_app and 'custom_relations' in selected_app.get('metadata', {}):
                            for relation in selected_app.get('metadata', {}).get('custom_relations', []):
                                # Добавляем с emoji для визуального отличия
                                role_options.append((relation, f"🔧 {relation.capitalize()}"))
                                custom_relations.append(relation)
                        
                        selected_role_index = st.selectbox(
                                "Выберите роль",
                            range(len(role_options)),
                            format_func=lambda i: role_options[i][1],
                            key="role_to_assign"
                            )
                        selected_role = role_options[selected_role_index][0]
                            
                    with col3:
                        st.write(" ")
                        st.write(" ")
                        if st.button("➕ Добавить", key="add_user_to_app", type="primary"):
                                success, message = self.controller.assign_user_to_app(
                                selected_app.get('name'),
                                selected_app.get('id'),
                                selected_user.get('id'),
                                    selected_role,
                                    tenant_id
                                )
                                if success:
                                    st.success(f"Роль назначена пользователю")
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.warning("Нет доступных пользователей. Создайте пользователей в разделе 'Пользователи'.")
            
            # Управление группами
            else:
                st.subheader(f"Управление группами для объекта: {selected_app['display_name']}")
                
                # Информация о доступных действиях
                with st.expander("ℹ️ Доступ групп к действиям", expanded=True):
                    # Показываем, какие действия доступны для групп
                    actions_with_group_access = [action.get('name') for action in selected_app.get('actions', []) 
                                             if action.get('group_allowed', False)]
                    
                    if actions_with_group_access:
                        st.markdown("**Действия, доступные для групп:**")
                        st.write(", ".join(actions_with_group_access))
                    else:
                        st.warning("⚠️ Ни одно действие не разрешено для групп. Группы не смогут выполнять никакие действия.")
                    
                # Таблица текущих групп
                app_groups = selected_app.get('groups', [])
                if app_groups:
                    st.markdown("#### Текущие группы с доступом")
                    groups_data = []
                    for group_id in app_groups:
                        # Находим информацию о группе
                        group_info = next((group for group in groups if group.get('id') == group_id), 
                                         {"id": group_id, "name": f"Группа {group_id}"})
                        
                        groups_data.append({
                            "ID": group_id,
                            "Название": group_info.get('name', f"Группа {group_id}"),
                            "Участников": len(group_info.get('members', []))
                                })
                            
                    if groups_data:
                        st.dataframe(
                            pd.DataFrame(groups_data),
                            use_container_width=True,
                            hide_index=True
                        )
                        
                        # Удаление группы
                        st.markdown("#### Удалить группу")
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            group_to_remove = st.selectbox(
                                "Выберите группу для удаления",
                                app_groups,
                                format_func=lambda x: next((g.get('name', f"Группа {g.get('id')}") 
                                                          for g in groups if g.get('id') == x), f"Группа {x}"),
                                key="group_to_remove"
                            )
                            
                        with col2:
                            st.write(" ")
                            st.write(" ")
                            if st.button("❌ Удалить", key="remove_group_from_app"):
                                success, message = self.controller.remove_group_from_app(
                                    selected_app.get('name'),
                                    selected_app.get('id'),
                                    group_to_remove,
                                    tenant_id
                                )
                                if success:
                                    st.success(f"Группа удалена из объекта")
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.info("Нет групп с доступом к этому объекту")
                
                # Добавление группы
                st.markdown("#### Добавить группу с доступом")
                
                # Фильтруем группы, которые еще не имеют доступа
                available_groups = [g for g in groups if g.get('id') not in app_groups]
                
                if available_groups:
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        selected_group = st.selectbox(
                            "Выберите группу",
                            [g.get('id') for g in available_groups],
                            format_func=lambda x: next((g.get('name', f"Группа {g.get('id')}") 
                                                      for g in available_groups if g.get('id') == x), f"Группа {x}"),
                            key="group_to_add"
                        )
                        
                    with col2:
                        st.write(" ")
                        st.write(" ")
                        if st.button("➕ Добавить", key="add_group_to_app", type="primary"):
                            success, message = self.controller.assign_group_to_app(
                                selected_app.get('name'),
                                selected_app.get('id'),
                                selected_group,
                                tenant_id
                            )
                            if success:
                                st.success(f"Группе предоставлен доступ")
                                st.rerun()
                            else:
                                st.error(message)
                else:
                    if groups:
                        st.info("Все имеющиеся группы уже имеют доступ к этому объекту")
                    else:
                        st.warning("Нет доступных групп. Создайте группы в разделе 'Группы'.")
        else:
            st.warning("Объекты не найдены. Создайте новый объект, используя форму выше.") 