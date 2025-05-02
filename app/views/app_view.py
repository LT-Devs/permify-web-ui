import streamlit as st
import pandas as pd
from .base_view import BaseView
from app.controllers import AppController, UserController, GroupController

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
        
        # Создание нового приложения
        with st.expander("Создать новое приложение"):
            col1, col2 = st.columns(2)
            with col1:
                new_app_name = st.text_input("Название приложения (без пробелов, латиницей)", "")
            with col2:
                new_app_id = st.text_input("ID приложения", "1")
            
            # Добавление действий для приложения
            st.subheader("Настройка действий")
            
            if 'app_actions' not in st.session_state:
                st.session_state.app_actions = [{"name": "", "editor_allowed": False, "viewer_allowed": False, "group_allowed": False}]
            
            # Отображаем существующие действия
            for i, action in enumerate(st.session_state.app_actions):
                cols = st.columns([3, 2, 2, 2, 1])
                with cols[0]:
                    st.session_state.app_actions[i]["name"] = st.text_input(
                        "Название действия", 
                        action["name"], 
                        key=f"action_name_{i}"
                    )
                
                with cols[1]:
                    st.session_state.app_actions[i]["editor_allowed"] = st.checkbox(
                        "Редакторы", 
                        action["editor_allowed"],
                        key=f"editor_{i}"
                    )
                
                with cols[2]:
                    st.session_state.app_actions[i]["viewer_allowed"] = st.checkbox(
                        "Просмотрщики", 
                        action["viewer_allowed"],
                        key=f"viewer_{i}"
                    )
                
                with cols[3]:
                    st.session_state.app_actions[i]["group_allowed"] = st.checkbox(
                        "Группы", 
                        action["group_allowed"],
                        key=f"groups_{i}"
                    )
                
                with cols[4]:
                    if st.button("❌", key=f"remove_action_{i}"):
                        if len(st.session_state.app_actions) > 1:
                            st.session_state.app_actions.pop(i)
                            st.rerun()
            
            # Кнопка для добавления нового действия
            if st.button("Добавить действие"):
                st.session_state.app_actions.append(
                    {"name": "", "editor_allowed": False, "viewer_allowed": False, "group_allowed": False}
                )
                st.rerun()
            
            # Кнопка для создания приложения
            if st.button("Создать приложение", key="create_app"):
                if new_app_name and new_app_id:
                    # Проверка на пустые или невалидные имена действий
                    valid_actions = [action for action in st.session_state.app_actions 
                                    if action["name"].strip() and action["name"].isalnum()]
                    
                    if not valid_actions:
                        st.error("Добавьте хотя бы одно действие с валидным названием (только буквы и цифры)")
                    else:
                        success, message = self.controller.create_app(new_app_name, new_app_id, valid_actions, tenant_id)
                        
                        if success:
                            st.success(message)
                            # Сбрасываем состояние действий
                            st.session_state.app_actions = [{"name": "", "editor_allowed": False, "viewer_allowed": False, "group_allowed": False}]
                            st.rerun()
                        else:
                            st.error(message)
                else:
                    st.warning("Введите название и ID приложения")
        
        # Получаем список приложений
        apps = self.controller.get_apps(tenant_id)
        
        if not apps:
            st.info("Приложения не найдены. Создайте новое приложение.")
            return
        
        # Получаем списки пользователей и групп для выбора
        users = self.user_controller.get_users(tenant_id)
        groups = self.group_controller.get_groups(tenant_id)
        
        # Отображаем список приложений с возможностью редактирования
        st.subheader("Список приложений")
        
        # Сначала показываем шаблоны приложений
        templates = [app for app in apps if app.get('is_template', False)]
        if templates:
            st.write("**Шаблоны приложений:**")
            for template in templates:
                with st.expander(f"Шаблон: {template.get('display_name')}"):
                    st.write(f"**Название:** {template.get('name')}")
                    
                    # Отображаем действия
                    st.write("**Доступные действия:**")
                    if template.get('actions'):
                        for action in template.get('actions'):
                            st.write(f"- {action.get('name')}: {action.get('description', '')}")
                    else:
                        st.write("Действия не определены")
                    
                    # Форма для создания экземпляра приложения
                    st.write("**Создать экземпляр приложения:**")
                    instance_id = st.text_input("ID экземпляра", "1", key=f"instance_id_{template.get('name')}")
                    
                    if st.button("Создать экземпляр", key=f"create_instance_{template.get('name')}"):
                        success, message = self.controller.create_app(
                            template.get('name'), 
                            instance_id, 
                            template.get('actions', []),
                            tenant_id
                        )
                        if success:
                            st.success(f"Экземпляр приложения {template.get('name')} создан")
                            st.rerun()
                        else:
                            st.error(message)
        
        # Отображаем экземпляры приложений
        instances = [app for app in apps if not app.get('is_template', False)]
        if instances:
            st.write("**Экземпляры приложений:**")
            for app in instances:
                with st.expander(f"{app.get('display_name')} (ID: {app.get('id')})"):
                    st.write(f"**Название:** {app.get('name')}")
                    st.write(f"**ID:** {app.get('id')}")
                    
                    # Отображаем действия
                    st.write("**Действия:**")
                    if app.get('actions'):
                        for action in app.get('actions'):
                            st.write(f"- {action.get('name')}: {action.get('description', '')}")
                    else:
                        st.write("Действия не определены")
                    
                    # Отображаем пользователей с ролями
                    st.write("**Пользователи с ролями:**")
                    users_with_roles = app.get('users', [])
                    
                    if users_with_roles:
                        for user_role in users_with_roles:
                            user_id = user_role.get('user_id')
                            role = user_role.get('role')
                            
                            # Находим имя пользователя, если есть
                            user_name = f"Пользователь {user_id}"
                            for user in users:
                                if user.get('id') == user_id:
                                    user_name = user.get('name', user_name)
                                    break
                            
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                st.write(f"- {user_name} (ID: {user_id}): {role}")
                            with col2:
                                if st.button("Удалить", key=f"remove_user_{app['name']}_{app['id']}_{user_id}_{role}"):
                                    success, message = self.controller.remove_user_from_app(
                                        app.get('name'),
                                        app.get('id'),
                                        user_id,
                                        role,
                                        tenant_id
                                    )
                                    if success:
                                        st.success(f"Пользователь {user_id} удален из приложения")
                                        st.rerun()
                                    else:
                                        st.error(message)
                    else:
                        st.write("Нет пользователей с ролями")
                    
                    # Добавление пользователя с ролью
                    if users:
                        st.write("**Добавить пользователя:**")
                        
                        # Получаем список пользователей
                        user_options = []
                        for user in users:
                            user_options.append({
                                "id": user.get('id'),
                                "name": user.get('name', f"Пользователь {user.get('id')}")
                            })
                        
                        if user_options:
                            selected_user_index = st.selectbox(
                                "Выберите пользователя",
                                range(len(user_options)),
                                format_func=lambda i: f"{user_options[i]['name']} (ID: {user_options[i]['id']})",
                                key=f"user_select_{app['name']}_{app['id']}"
                            )
                            
                            selected_user = user_options[selected_user_index]
                            selected_role = st.selectbox(
                                "Выберите роль",
                                ["owner", "editor", "viewer"],
                                key=f"role_select_{app['name']}_{app['id']}"
                            )
                            
                            if st.button("Назначить роль", key=f"add_user_{app['name']}_{app['id']}"):
                                success, message = self.controller.assign_user_to_app(
                                    app.get('name'),
                                    app.get('id'),
                                    selected_user["id"],
                                    selected_role,
                                    tenant_id
                                )
                                if success:
                                    st.success(f"Пользователю {selected_user['id']} назначена роль {selected_role}")
                                    st.rerun()
                                else:
                                    st.error(message)
                    
                    # Отображаем группы с доступом
                    st.write("**Группы с доступом:**")
                    groups_with_access = app.get('groups', [])
                    
                    if groups_with_access:
                        for group_id in groups_with_access:
                            # Находим имя группы, если есть
                            group_name = f"Группа {group_id}"
                            for group in groups:
                                if group.get('id') == group_id:
                                    group_name = group.get('name', group_name)
                                    break
                            
                            col1, col2 = st.columns([5, 1])
                            with col1:
                                st.write(f"- {group_name} (ID: {group_id})")
                            with col2:
                                if st.button("Удалить", key=f"remove_group_{app['name']}_{app['id']}_{group_id}"):
                                    success, message = self.controller.remove_group_from_app(
                                        app.get('name'),
                                        app.get('id'),
                                        group_id,
                                        tenant_id
                                    )
                                    if success:
                                        st.success(f"Группа {group_id} удалена из приложения")
                                        st.rerun()
                                    else:
                                        st.error(message)
                    else:
                        st.write("Нет групп с доступом")
                    
                    # Добавление группы
                    if groups:
                        st.write("**Добавить группу:**")
                        
                        # Фильтруем группы, которые еще не имеют доступа
                        available_groups = [g for g in groups if g.get('id') not in groups_with_access]
                        
                        if available_groups:
                            group_options = []
                            for group in available_groups:
                                group_options.append({
                                    "id": group.get('id'),
                                    "name": group.get('name', f"Группа {group.get('id')}")
                                })
                            
                            selected_group_index = st.selectbox(
                                "Выберите группу",
                                range(len(group_options)),
                                format_func=lambda i: f"{group_options[i]['name']} (ID: {group_options[i]['id']})",
                                key=f"group_select_{app['name']}_{app['id']}"
                            )
                            
                            if st.button("Добавить группу", key=f"add_group_{app['name']}_{app['id']}"):
                                selected_group = group_options[selected_group_index]
                                success, message = self.controller.assign_group_to_app(
                                    app.get('name'),
                                    app.get('id'),
                                    selected_group["id"],
                                    tenant_id
                                )
                                if success:
                                    st.success(f"Группе {selected_group['id']} предоставлен доступ")
                                    st.rerun()
                                else:
                                    st.error(message)
                    
                    # Тестирование прав доступа
                    st.write("**Проверка прав доступа:**")
                    
                    if app.get('actions'):
                        test_user_id = st.text_input(
                            "ID пользователя для проверки", 
                            "", 
                            key=f"test_user_{app['name']}_{app['id']}"
                        )
                        
                        selected_action = st.selectbox(
                            "Выберите действие",
                            [action.get('name') for action in app.get('actions')],
                            key=f"test_action_{app['name']}_{app['id']}"
                        )
                        
                        if st.button("Проверить доступ", key=f"check_access_{app['name']}_{app['id']}"):
                            if test_user_id:
                                success, result = self.controller.check_user_permission(
                                    app.get('name'),
                                    app.get('id'),
                                    test_user_id,
                                    selected_action,
                                    tenant_id
                                )
                                
                                if success:
                                    if result.get("can") or result.get("can") == "CHECK_RESULT_ALLOWED":
                                        st.success(f"✅ Пользователь {test_user_id} имеет разрешение {selected_action}")
                                    else:
                                        st.error(f"❌ Пользователь {test_user_id} не имеет разрешения {selected_action}")
                                else:
                                    st.error(f"Ошибка проверки: {result}")
                            else:
                                st.warning("Введите ID пользователя для проверки") 