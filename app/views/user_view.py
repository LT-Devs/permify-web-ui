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
        
        # Получаем список пользователей
        users = self.controller.get_users(tenant_id)
        
        # Получаем списки групп и приложений для выбора
        groups = self.group_controller.get_groups(tenant_id)
        apps = self.app_controller.get_apps(tenant_id)
        
        # Создание нового пользователя
        with st.container():
            st.subheader("Создать нового пользователя")
            
            col1, col2, col3 = st.columns([2, 2, 1])
            with col1:
                new_user_id = st.text_input("ID пользователя", key="new_user_id")
            with col2:
                new_user_name = st.text_input("Имя пользователя", key="new_user_name")
            with col3:
                st.write("")
                st.write("")
                create_button = st.button("Создать пользователя", type="primary", key="create_user")
            
            if create_button:
                if not new_user_id:
                    st.error("Введите ID пользователя")
                else:
                    success, message = self.controller.create_user(new_user_id, new_user_name, tenant_id)
                    if success:
                        st.success(message)
                        # Перезагружаем страницу для обновления списка
                        st.rerun()
                    else:
                        st.error(message)
        
        # Отображаем обзор пользователей
        if users:
            st.subheader("Обзор пользователей")
            
            # Создаем таблицу пользователей для обзора
            user_data = []
            for user in users:
                user_groups = user.get('groups', [])
                group_names = ", ".join([f"Группа {g}" for g in user_groups]) if user_groups else "Нет"
                
                app_roles = user.get('app_roles', [])
                role_names = ", ".join([f"{role.get('app_type')}:{role.get('role')}" for role in app_roles]) if app_roles else "Нет"
                
                user_data.append({
                    "ID": user.get('id'),
                    "Имя": user.get('name', f"Пользователь {user.get('id')}"),
                    "Группы": group_names,
                    "Права доступа": role_names
                })
            
            if user_data:
                st.dataframe(
                    pd.DataFrame(user_data),
                    use_container_width=True,
                    hide_index=True
                )
        else:
            st.info("Пользователи не найдены. Создайте нового пользователя.")
        
        # Управление пользователями
        if users:
            st.subheader("Управление правами доступа")
            
            # Выбор пользователя для управления
            selected_user_id = st.selectbox(
                "Выберите пользователя для управления",
                [user.get('id') for user in users],
                format_func=lambda x: next((user.get('name', f"Пользователь {user.get('id')}") for user in users if user.get('id') == x), x),
                key="select_user"
            )
            
            # Находим выбранного пользователя
            selected_user = next((user for user in users if user.get('id') == selected_user_id), None)
            
            if selected_user:
                # Добавляем кнопку удаления пользователя в отдельном блоке
                delete_col1, delete_col2 = st.columns([4, 1])
                with delete_col1:
                    st.warning(f"Удаление пользователя **{selected_user.get('name', selected_user_id)}** приведет к удалению всех его отношений и ролей.")
                with delete_col2:
                    if st.button("🗑️ Удалить пользователя", key=f"delete_user_{selected_user_id}", type="primary"):
                        st.session_state["confirm_delete_user"] = selected_user_id
                        st.rerun()
                
                # Подтверждение удаления
                if "confirm_delete_user" in st.session_state and st.session_state["confirm_delete_user"] == selected_user_id:
                    st.warning("Вы уверены, что хотите удалить пользователя? Это действие нельзя отменить.")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Да, удалить", key="confirm_delete_yes"):
                            success, message = self.controller.delete_user(selected_user_id, tenant_id)
                            if success:
                                st.success(message)
                                # Очищаем состояние и перезагружаем страницу
                                del st.session_state["confirm_delete_user"]
                                # Перезагружаем страницу для обновления списка
                                st.rerun()
                            else:
                                st.error(message)
                    with col2:
                        if st.button("Отмена", key="confirm_delete_no"):
                            del st.session_state["confirm_delete_user"]
                            st.rerun()
                
                tabs = st.tabs(["Членство в группах", "Права в приложениях"])
                
                # Управление группами
                with tabs[0]:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Текущие группы")
                        user_groups = selected_user.get('groups', [])
                        
                        if user_groups:
                            for group_id in user_groups:
                                col_a, col_b = st.columns([4, 1])
                                with col_a:
                                    group_name = next((g.get('name', f"Группа {g.get('id')}") for g in groups if g.get('id') == group_id), f"Группа {group_id}")
                                    st.write(f"- {group_name}")
                                with col_b:
                                    if st.button("Удалить", key=f"remove_group_{selected_user_id}_{group_id}"):
                                        success, message = self.controller.remove_user_from_group(selected_user_id, group_id, tenant_id)
                                        if success:
                                            st.success(f"Пользователь удален из группы")
                                            st.rerun()
                                        else:
                                            st.error(message)
                        else:
                            st.info("Пользователь не состоит в группах")
                    
                    with col2:
                        st.subheader("Добавить в группу")
                        available_groups = [g for g in groups if g.get('id') not in selected_user.get('groups', [])]
                        
                        if available_groups:
                            selected_group = st.selectbox(
                                "Выберите группу",
                                [g.get('id') for g in available_groups],
                                format_func=lambda x: next((g.get('name', f"Группа {g.get('id')}") for g in available_groups if g.get('id') == x), x),
                                key=f"add_group_to_user"
                            )
                            
                            if st.button("Добавить в группу", key=f"user_view_add_user_to_group_{selected_user_id}", type="primary"):
                                success, message = self.controller.add_user_to_group(
                                    selected_user_id, selected_group, tenant_id
                                )
                                if success:
                                    st.success(f"Пользователь добавлен в группу")
                                    st.rerun()
                                else:
                                    st.error(message)
                        else:
                            st.info("Нет доступных групп для добавления")
                
                # Управление ролями в приложениях
                with tabs[1]:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.subheader("Текущие права в приложениях")
                        user_roles = selected_user.get('app_roles', [])
                        
                        if user_roles:
                            for role in user_roles:
                                app_type = role.get('app_type')
                                app_id = role.get('app_id')
                                role_name = role.get('role')
                                
                                # Преобразуем стандартные роли в удобочитаемый формат
                                standard_roles = {
                                    "owner": "👑 Владелец (полный доступ)",
                                    "editor": "✏️ Редактор",
                                    "viewer": "👁️ Просмотрщик"
                                }
                                display_role = standard_roles.get(role_name, f"🔧 {role_name.capitalize()}")
                                
                                col_a, col_b = st.columns([4, 1])
                                with col_a:
                                    app_display = next((app.get('display_name', app.get('name')) for app in apps if app.get('name') == app_type and app.get('id') == app_id), f"{app_type}")
                                    st.write(f"- {app_display} (ID: {app_id}): **{display_role}**")
                                with col_b:
                                    if st.button("Удалить", key=f"remove_role_{selected_user_id}_{app_type}_{app_id}_{role_name}"):
                                        success, message = self.controller.remove_app_role(
                                            selected_user_id, app_type, app_id, role_name, tenant_id
                                        )
                                        if success:
                                            st.success(f"Роль удалена")
                                            st.rerun()
                                        else:
                                            st.error(message)
                        else:
                            st.info("Пользователь не имеет прав в приложениях")
                    
                    with col2:
                        st.subheader("Назначить права в приложении")
                        
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
                                key=f"app_select_for_user"
                            )
                            
                            selected_app = app_options[selected_app_index]
                            
                            col_role, col_btn = st.columns([2, 1])
                            with col_role:
                                # Получаем стандартные роли
                                role_options = [
                                    ("owner", "👑 Владелец (полный доступ)"),
                                    ("editor", "✏️ Редактор (может изменять)"),
                                    ("viewer", "👁️ Просмотрщик (только чтение)")
                                ]
                                
                                # Ищем приложение в списке приложений для получения пользовательских ролей
                                app_obj = next((app for app in apps if app.get('name') == selected_app["name"] and app.get('id') == selected_app["id"]), None)
                                if app_obj and 'metadata' in app_obj and 'custom_relations' in app_obj.get('metadata', {}):
                                    for relation in app_obj.get('metadata', {}).get('custom_relations', []):
                                        # Добавляем с emoji для визуального отличия
                                        role_options.append((relation, f"🔧 {relation.capitalize()}"))
                                
                                selected_role_index = st.selectbox(
                                    "Выберите роль",
                                    range(len(role_options)),
                                    format_func=lambda i: role_options[i][1],
                                    key=f"role_select_for_user"
                                )
                                selected_role = role_options[selected_role_index][0]
                            with col_btn:
                                st.write("")
                                if st.button("Назначить", key=f"assign_role_to_user", type="primary"):
                                    success, message = self.controller.assign_app_role(
                                        selected_user_id, 
                                        selected_app["name"], 
                                        selected_app["id"], 
                                        selected_role, 
                                        tenant_id
                                    )
                                    if success:
                                        st.success(f"Роль назначена успешно")
                                        st.rerun()
                                    else:
                                        st.error(message)
                        else:
                            st.info("Нет доступных приложений")
            else:
                st.warning("Пользователь не найден") 