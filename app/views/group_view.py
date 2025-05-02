import streamlit as st
import pandas as pd
from .base_view import BaseView
from app.controllers import GroupController, UserController, AppController

class GroupView(BaseView):
    """Представление для управления группами в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.controller = GroupController()
        self.user_controller = UserController()
        self.app_controller = AppController()
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс управления группами."""
        self.show_header("Управление группами", 
                         "Создание и редактирование групп, назначение пользователей и доступ к приложениям")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("group_view")
        
        # Создание новой группы
        with st.expander("Создать новую группу"):
            col1, col2 = st.columns(2)
            with col1:
                new_group_id = st.text_input("ID группы", "")
            with col2:
                new_group_name = st.text_input("Название группы", "")
            
            if st.button("Создать группу", key="create_group"):
                if new_group_id:
                    success, message = self.controller.create_group(new_group_id, new_group_name, tenant_id)
                    if success:
                        st.success(message)
                    else:
                        st.error(message)
                else:
                    st.warning("Введите ID группы")
        
        # Получаем список групп
        groups = self.controller.get_groups(tenant_id)
        
        if not groups:
            st.info("Группы не найдены. Создайте новую группу.")
            return
        
        # Получаем списки пользователей и приложений для выбора
        users = self.user_controller.get_users(tenant_id)
        apps = self.app_controller.get_apps(tenant_id)
        
        # Отображаем список групп с возможностью редактирования
        st.subheader("Список групп")
        
        for group in groups:
            with st.expander(f"Группа: {group.get('name', f'ID {group.get('id')}')}"):
                st.write(f"**ID группы:** {group.get('id')}")
                
                # Отображаем участников группы
                st.write("**Участники группы:**")
                group_members = group.get('members', [])
                
                if group_members:
                    for user_id in group_members:
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            # Находим имя пользователя, если есть
                            user_name = f"Пользователь {user_id}"
                            for user in users:
                                if user.get('id') == user_id:
                                    user_name = user.get('name', user_name)
                                    break
                            
                            st.write(f"- {user_name} (ID: {user_id})")
                        with col2:
                            if st.button("Удалить", key=f"remove_user_{group['id']}_{user_id}"):
                                success, message = self.controller.remove_user_from_group(
                                    group.get('id'), user_id, tenant_id
                                )
                                if success:
                                    st.success(f"Пользователь {user_id} удален из группы")
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.write("В группе нет участников")
                
                # Добавление пользователя в группу
                if users:
                    # Фильтруем пользователей, которые еще не в группе
                    available_users = [u for u in users if u.get('id') not in group_members]
                    
                    if available_users:
                        user_options = [(u.get('id'), u.get('name', f"Пользователь {u.get('id')}")) 
                                      for u in available_users]
                        
                        selected_user_index = st.selectbox(
                            "Выберите пользователя для добавления", 
                            range(len(user_options)),
                            format_func=lambda i: f"{user_options[i][1]} (ID: {user_options[i][0]})",
                            key=f"user_select_{group['id']}"
                        )
                        
                        if st.button("Добавить пользователя", key=f"add_user_{group['id']}"):
                            selected_user_id = user_options[selected_user_index][0]
                            success, message = self.controller.add_user_to_group(
                                group.get('id'), selected_user_id, tenant_id
                            )
                            if success:
                                st.success(f"Пользователь {selected_user_id} добавлен в группу")
                                st.rerun()
                            else:
                                st.error(message)
                
                # Отображаем связи с приложениями
                st.write("**Доступ к приложениям:**")
                app_memberships = group.get('app_memberships', [])
                
                if app_memberships:
                    for app_membership in app_memberships:
                        app_type = app_membership.get('app_type')
                        app_id = app_membership.get('app_id')
                        
                        col1, col2 = st.columns([5, 1])
                        with col1:
                            st.write(f"- {app_type.capitalize()} (ID: {app_id})")
                        with col2:
                            if st.button("Удалить", key=f"remove_app_{group['id']}_{app_type}_{app_id}"):
                                success, message = self.controller.remove_group_from_app(
                                    group.get('id'), app_type, app_id, tenant_id
                                )
                                if success:
                                    st.success(f"Группа удалена из приложения {app_type}")
                                    st.rerun()
                                else:
                                    st.error(message)
                else:
                    st.write("Группа не имеет доступа к приложениям")
                
                # Добавление доступа к приложению
                if apps:
                    # Фильтруем приложения, исключая шаблоны
                    app_instances = [app for app in apps 
                                   if not app.get('is_template', False) and app.get('id')]
                    
                    if app_instances:
                        # Создаем список приложений для выбора
                        app_options = []
                        for app in app_instances:
                            # Проверяем, имеет ли группа уже доступ к этому приложению
                            already_has_access = any(
                                membership.get('app_type') == app.get('name') and 
                                membership.get('app_id') == app.get('id')
                                for membership in app_memberships
                            )
                            
                            if not already_has_access:
                                app_options.append({
                                    "display": f"{app.get('display_name')} (ID: {app.get('id')})",
                                    "name": app.get('name'),
                                    "id": app.get('id')
                                })
                        
                        if app_options:
                            selected_app_index = st.selectbox(
                                "Выберите приложение для доступа",
                                range(len(app_options)),
                                format_func=lambda i: app_options[i]["display"],
                                key=f"app_select_{group['id']}"
                            )
                            
                            if st.button("Предоставить доступ", key=f"grant_access_{group['id']}"):
                                selected_app = app_options[selected_app_index]
                                success, message = self.controller.assign_group_to_app(
                                    group.get('id'),
                                    selected_app["name"],
                                    selected_app["id"],
                                    tenant_id
                                )
                                if success:
                                    st.success(f"Группе предоставлен доступ к приложению {selected_app['name']}")
                                    st.rerun()
                                else:
                                    st.error(message) 