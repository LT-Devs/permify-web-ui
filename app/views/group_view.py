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
        
        # Получаем списки групп, пользователей и приложений
        groups = self.controller.get_groups(tenant_id)
        users = self.user_controller.get_users(tenant_id)
        apps = self.app_controller.get_apps(tenant_id)
        
        # Создание новой группы
        with st.container():
            st.subheader("Создать новую группу")
            
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                new_group_id = st.text_input("ID группы", key="new_group_id")
            with col2:
                new_group_name = st.text_input("Название группы", key="new_group_name")
            with col3:
                st.write("")
                st.write("")
                create_button = st.button("Создать группу", type="primary", key="create_group")
            
            if create_button:
                if not new_group_id:
                    st.error("Введите ID группы")
                else:
                    success, message = self.controller.create_group(new_group_id, new_group_name, tenant_id)
                    if success:
                        st.success(message)
                        # Перезагружаем страницу для обновления списка
                        st.rerun()
                    else:
                        st.error(message)
        
        # Отображаем обзор групп
        if groups:
            st.subheader("Обзор групп")
            
            # Создаем таблицу групп для обзора
            group_data = []
            for group in groups:
                members_count = len(group.get('members', []))
                app_memberships = group.get('app_memberships', [])
                app_names = ", ".join([f"{app.get('app_type')}:{app.get('app_id')}" for app in app_memberships]) if app_memberships else "Нет"
                
                group_data.append({
                    "ID": group.get('id'),
                    "Название": group.get('name', f"Группа {group.get('id')}"),
                    "Участников": members_count,
                    "Доступ к приложениям": app_names
                })
            
            if group_data:
                st.dataframe(
                    pd.DataFrame(group_data),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("Группы не найдены. Создайте новую группу.")
        
        # Управление группами
        if groups:
            st.subheader("Управление группами")
            
            # Выбор группы для управления
            selected_group_id = st.selectbox(
                "Выберите группу для управления",
                [group.get('id') for group in groups],
                format_func=lambda x: next((group.get('name', f"Группа {group.get('id')}") for group in groups if group.get('id') == x), x),
                key="select_group"
            )
            
            # Находим выбранную группу
            selected_group = next((group for group in groups if group.get('id') == selected_group_id), None)
            
            if selected_group:
                tabs = st.tabs(["Участники группы", "Доступ к приложениям"])
                
                # Управление участниками группы
                with tabs[0]:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Текущие участники")
                        group_members = selected_group.get('members', [])
                        
                        if group_members:
                            for user_id in group_members:
                                col_a, col_b = st.columns([4, 1])
                                with col_a:
                                    # Находим имя пользователя, если есть
                                    user_name = next((user.get('name', f"Пользователь {user.get('id')}") for user in users if user.get('id') == user_id), f"Пользователь {user_id}")
                                    st.write(f"- {user_name} (ID: {user_id})")
                                with col_b:
                                    if st.button("Удалить", key=f"remove_user_{selected_group_id}_{user_id}"):
                                        success, message = self.controller.remove_user_from_group(
                                            selected_group_id, user_id, tenant_id
                                        )
                                        if success:
                                            st.success(f"Пользователь удален из группы")
                                            st.rerun()
                                        else:
                                            st.error(message)
                        else:
                            st.info("В группе нет участников")
                    
                    with col2:
                        st.subheader("Добавить участника")
                        
                        # Фильтруем пользователей, которые еще не в группе
                        available_users = [u for u in users if u.get('id') not in selected_group.get('members', [])]
                        
                        if available_users:
                            selected_user = st.selectbox(
                                "Выберите пользователя",
                                [u.get('id') for u in available_users],
                                format_func=lambda x: next((u.get('name', f"Пользователь {u.get('id')}") for u in available_users if u.get('id') == x), x),
                                key=f"group_view_add_user_to_group_{selected_group_id}"
                            )
                            
                            if st.button("Добавить участника", key=f"add_user_{selected_group_id}", type="primary"):
                                success, message = self.controller.add_user_to_group(
                                    selected_group_id, selected_user, tenant_id
                                )
                                if success:
                                    st.success(f"Пользователь добавлен в группу")
                                    st.rerun()
                                else:
                                    st.error(message)
                        else:
                            st.info("Нет доступных пользователей для добавления")
                
                # Управление доступом к приложениям
                with tabs[1]:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Текущий доступ к приложениям")
                        app_memberships = selected_group.get('app_memberships', [])
                        
                        if app_memberships:
                            for app_membership in app_memberships:
                                app_type = app_membership.get('app_type')
                                app_id = app_membership.get('app_id')
                                
                                col_a, col_b = st.columns([4, 1])
                                with col_a:
                                    app_display = next((app.get('display_name', app.get('name')) for app in apps if app.get('name') == app_type and app.get('id') == app_id), f"{app_type}")
                                    st.write(f"- {app_display} (ID: {app_id})")
                                with col_b:
                                    if st.button("Удалить", key=f"remove_app_{selected_group_id}_{app_type}_{app_id}"):
                                        success, message = self.controller.remove_group_from_app(
                                            selected_group_id, app_type, app_id, tenant_id
                                        )
                                        if success:
                                            st.success(f"Доступ к приложению удален")
                                            st.rerun()
                                        else:
                                            st.error(message)
                        else:
                            st.info("Группа не имеет доступа к приложениям")
                    
                    with col2:
                        st.subheader("Предоставить доступ к приложению")
                        
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
                                    "Выберите приложение",
                                    range(len(app_options)),
                                    format_func=lambda i: app_options[i]["display"],
                                    key=f"app_select_for_group"
                                )
                                
                                if st.button("Предоставить доступ", key=f"grant_access_{selected_group_id}", type="primary"):
                                    selected_app = app_options[selected_app_index]
                                    success, message = self.controller.assign_group_to_app(
                                        selected_group_id,
                                        selected_app["name"],
                                        selected_app["id"],
                                        tenant_id
                                    )
                                    if success:
                                        st.success(f"Доступ к приложению предоставлен")
                                        st.rerun()
                                    else:
                                        st.error(message)
                            else:
                                st.info("Нет доступных приложений для предоставления доступа")
                        else:
                            st.info("Нет доступных приложений")
            else:
                st.warning("Группа не найдена") 