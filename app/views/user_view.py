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
                    st.subheader("Управление правами в приложениях")
                    
                    # Фильтруем приложения
                    available_apps = []
                    for app in apps:
                        # Убедимся, что app_id существует
                        if 'id' not in app or not app['id']:
                            app['id'] = ''  # Установим пустую строку по умолчанию
                        available_apps.append(app)
                    
                    if available_apps:
                        # Выбор приложения
                        selected_app = st.selectbox(
                            "Выберите приложение",
                            [f"{app.get('name', 'Unknown')}:{app.get('id', '')}" for app in available_apps if 'name' in app],
                            format_func=lambda x: next((f"{app.get('display_name', app.get('name'))} (ID: {app.get('id', '')})" 
                                                for app in available_apps 
                                                if f"{app.get('name', 'Unknown')}:{app.get('id', '')}" == x), x),
                            key=f"app_access_app_select_{selected_user_id}"
                        )
                        
                        if selected_app:
                            app_type, app_id = selected_app.split(":")
                            
                            # Находим выбранное приложение
                            selected_app_obj = next((app for app in available_apps 
                                                if app.get('name') == app_type and app.get('id') == app_id), None)
                            
                            # Получаем текущие роли пользователя для этого приложения
                            current_roles = []
                            current_roles_original = []  # Для хранения оригинальных имен ролей
                            
                            for app_role in selected_user.get('app_roles', []):
                                if app_role.get('app_type') == app_type and app_role.get('app_id') == app_id:
                                    # Сохраняем оригинальное имя роли для последующего удаления
                                    role_original = app_role.get('role', '')
                                    current_roles_original.append(role_original)
                                    current_roles.append(role_original.lower())  # Приводим к нижнему регистру
                            
                            # Определяем стандартные роли
                            standard_roles = [
                                {"value": "owner", "label": "👑 Владелец (полный доступ)"},
                                {"value": "editor", "label": "✏️ Редактор (изменение)"},
                                {"value": "viewer", "label": "👁️ Просмотрщик (только чтение)"}
                            ]
                            
                            # Добавляем кастомные роли из метаданных приложения
                            custom_roles = []
                            if selected_app_obj and 'metadata' in selected_app_obj and 'custom_relations' in selected_app_obj.get('metadata', {}):
                                custom_relations = selected_app_obj.get('metadata', {}).get('custom_relations', [])
                                for relation in custom_relations:
                                    custom_roles.append({"value": relation.lower(), "label": f"🔧 {relation.capitalize()}"})
                            
                            # Комбинируем все роли
                            all_roles = standard_roles + custom_roles
                            
                            # Создаем форму с чекбоксами
                            with st.form(key=f"user_roles_form_{selected_user_id}_{app_type}_{app_id}"):
                                st.write("**Выберите роли для пользователя:**")
                                
                                # Используем чекбоксы для выбора ролей
                                selected_roles = []
                                for role in all_roles:
                                    # Проверяем, есть ли роль в текущих ролях (приводим обе к нижнему регистру)
                                    is_checked = role["value"].lower() in current_roles
                                    if st.checkbox(role["label"], value=is_checked, key=f"user_role_checkbox_{selected_user_id}_{app_type}_{app_id}_{role['value']}"):
                                        selected_roles.append(role["value"])
                                
                                # Кнопка для сохранения изменений
                                submit_button = st.form_submit_button("Сохранить изменения", type="primary")
                                
                                if submit_button:
                                    try:
                                        # Норамализуем выбранные роли
                                        selected_roles_norm = [role.lower() for role in selected_roles]
                                        
                                        # Находим роли, которые нужно добавить (есть в selected_roles, но нет в current_roles)
                                        roles_to_add = []
                                        for i, role in enumerate(selected_roles):
                                            if selected_roles_norm[i] not in current_roles:
                                                roles_to_add.append(role)
                                        
                                        # Находим роли, которые нужно удалить
                                        roles_to_remove = []
                                        for role_original in current_roles_original:
                                            if role_original.lower() not in selected_roles_norm:
                                                roles_to_remove.append(role_original)
                                        
                                        # Отладочная информация
                                        st.write(f"DEBUG: Текущие роли (нормализованные): {current_roles}")
                                        st.write(f"DEBUG: Выбранные роли (нормализованные): {selected_roles_norm}")
                                        st.write(f"DEBUG: Роли для добавления: {roles_to_add}")
                                        st.write(f"DEBUG: Роли для удаления: {roles_to_remove}")
                                        
                                        # Сначала добавляем новые роли
                                        for role in roles_to_add:
                                            success, message = self.controller.assign_app_role(
                                                selected_user_id, app_type, app_id, role, tenant_id
                                            )
                                            
                                            if not success:
                                                st.warning(f"Не удалось добавить роль {role}: {message}")
                                        
                                        # Затем удаляем ненужные роли
                                        for role in roles_to_remove:
                                            success, message = self.controller.remove_app_role(
                                                selected_user_id, app_type, app_id, role, tenant_id
                                            )
                                            
                                            if not success:
                                                st.warning(f"Не удалось удалить роль {role}: {message}")
                                        
                                        st.success("Роли успешно обновлены")
                                        st.rerun()
                                    except Exception as e:
                                        import traceback
                                        st.error(f"Ошибка при обновлении ролей: {str(e)}")
                                        st.code(traceback.format_exc())
                    else:
                        st.info("Нет доступных приложений")
            else:
                st.warning("Пользователь не найден") 