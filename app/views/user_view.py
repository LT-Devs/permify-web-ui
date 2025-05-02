import streamlit as st
import pandas as pd
from .base_view import BaseView
from app.controllers import UserController, GroupController, AppController

class UserView(BaseView):
    """Представление для управления пользователями в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.controller = UserController()
        self.group_controller = GroupController()
        self.app_controller = AppController()
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс управления пользователями."""
        self.show_header("Управление пользователями", 
                         "Создание и редактирование пользователей, назначение групп и ролей в приложениях")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("user_view")
        
        # Создание нового пользователя
        with st.expander("Создать нового пользователя"):
            col1, col2 = st.columns(2)
            with col1:
                new_user_id = st.text_input("ID пользователя", "")
            with col2:
                new_user_name = st.text_input("Имя пользователя", "")
            
            if st.button("Создать пользователя", key="create_user"):
                if new_user_id:
                    success, message = self.controller.create_user(new_user_id, new_user_name, tenant_id)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Введите ID пользователя")
        
        # Получаем список пользователей
        users = self.controller.get_users(tenant_id)
        
        if not users:
            st.info("Пользователи не найдены. Создайте нового пользователя.")
            return
        
        # Получаем списки групп и приложений для выбора
        groups = self.group_controller.get_groups(tenant_id)
        apps = self.app_controller.get_apps(tenant_id)
        
        # Отображаем список пользователей с возможностью редактирования
        st.subheader("Список пользователей")
        
        for user in users:
            with st.expander(f"Пользователь: {user.get('name', f'ID {user.get('id')}')}"):
                st.write(f"**ID пользователя:** {user.get('id')}")
                
                # Отображаем группы пользователя
                st.write("**Группы:**")
                user_groups = user.get('groups', [])
                
                if user_groups:
                    for group_id in user_groups:
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.write(f"- Группа {group_id}")
                        with col2:
                            if st.button("Удалить", key=f"remove_group_{user['id']}_{group_id}"):
                                success, message = self.controller.remove_user_from_group(
                                    user.get('id'), group_id, tenant_id
                                )
                                if success:
                                    st.success(f"Пользователь удален из группы {group_id}")
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.write("Пользователь не состоит в группах")
                
                # Добавление в группу
                if groups:
                    group_options = [g.get('id') for g in groups if g.get('id') not in user_groups]
                    if group_options:
                        selected_group = st.selectbox(
                            "Выберите группу для добавления", 
                            group_options,
                            key=f"group_select_{user['id']}"
                        )
                        
                        if st.button("Добавить в группу", key=f"add_to_group_{user['id']}"):
                            success, message = self.controller.add_user_to_group(
                                user.get('id'), selected_group, tenant_id
                            )
                            if success:
                                st.success(f"Пользователь добавлен в группу {selected_group}")
                                st.rerun()
                            else:
                                st.error(message)
                
                # Отображаем роли в приложениях
                st.write("**Роли в приложениях:**")
                user_roles = user.get('app_roles', [])
                
                if user_roles:
                    for role in user_roles:
                        app_type = role.get('app_type')
                        app_id = role.get('app_id')
                        role_name = role.get('role')
                        
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.write(f"- {app_type.capitalize()} (ID: {app_id}): {role_name}")
                        with col2:
                            if st.button("Удалить", key=f"remove_role_{user['id']}_{app_type}_{app_id}_{role_name}"):
                                success, message = self.controller.remove_app_role(
                                    user.get('id'), app_type, app_id, role_name, tenant_id
                                )
                                if success:
                                    st.success(f"Роль {role_name} в приложении {app_type} удалена")
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.write("Пользователь не имеет ролей в приложениях")
                
                # Добавление роли в приложении
                if apps:
                    # Создаем список приложений для выбора
                    app_options = []
                    for app in apps:
                        if not app.get('is_template', False) and app.get('id'):  # Только реальные экземпляры
                            app_options.append({
                                "display": f"{app.get('display_name')} (ID: {app.get('id')})",
                                "name": app.get('name'),
                                "id": app.get('id')
                            })
                    
                    if app_options:
                        selected_app_index = st.selectbox(
                            "Выберите приложение",
                            range(len(app_options)),
                            format_func=lambda i: app_options[i]["display"],
                            key=f"app_select_{user['id']}"
                        )
                        
                        selected_app = app_options[selected_app_index]
                        selected_role = st.selectbox(
                            "Выберите роль",
                            ["owner", "editor", "viewer"],
                            key=f"role_select_{user['id']}"
                        )
                        
                        if st.button("Назначить роль", key=f"assign_role_{user['id']}"):
                            success, message = self.controller.assign_app_role(
                                user.get('id'), 
                                selected_app["name"], 
                                selected_app["id"], 
                                selected_role, 
                                tenant_id
                            )
                            if success:
                                st.success(f"Роль {selected_role} в приложении {selected_app['name']} назначена")
                                st.rerun()
                            else:
                                st.error(message) 