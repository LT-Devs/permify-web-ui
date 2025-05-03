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
                        label="",
                        value=action["name"], 
                        placeholder="Имя действия (например, view, edit, export)",
                        key=f"action_name_{i}"
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
                            success, message = self.controller.create_app(
                                new_app_name, new_app_id, valid_actions, tenant_id
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
                            st.session_state.edit_app_actions.append({
                                "name": action.get('name', ''),
                                "editor_allowed": action.get('editor_allowed', False),
                                "viewer_allowed": action.get('viewer_allowed', False),
                                "group_allowed": action.get('group_allowed', False)
                            })
                        st.session_state.current_edit_app = f"{selected_app['name']}:{selected_app['id']}"
                    
                    # Отображаем форму редактирования действий
                    st.markdown("### Редактирование действий (permissions)")
                    st.caption("Изменение разрешений для этого объекта")
        
                    # Используем тот же макет, что и для создания
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
                    for i, action in enumerate(st.session_state.edit_app_actions):
                        # Добавляем div с классом для стилизации строки
                        st.markdown(f'<div class="action-row">', unsafe_allow_html=True)
                        
                        cols = st.columns([3, 2, 2, 2, 1])
                        with cols[0]:
                            st.session_state.edit_app_actions[i]["name"] = st.text_input(
                                label="",
                                value=action["name"], 
                                placeholder="Имя действия (например, view, edit, export)",
                                key=f"edit_action_name_{i}"
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
                                success, message = self.controller.update_app(
                                    selected_app['name'], selected_app['id'], valid_actions, tenant_id
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
                        
                        role_display = {"owner": "Владелец", "editor": "Редактор", "viewer": "Просмотрщик"}.get(role, role)
                        
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