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
                # Добавляем кнопку удаления группы в отдельном блоке
                delete_col1, delete_col2 = st.columns([4, 1])
                with delete_col1:
                    st.warning(f"Удаление группы **{selected_group.get('name', selected_group_id)}** приведет к удалению всех её участников и отношений с приложениями.")
                with delete_col2:
                    if st.button("🗑️ Удалить группу", key=f"delete_group_{selected_group_id}", type="primary"):
                        st.session_state["confirm_delete_group"] = selected_group_id
                        st.rerun()
                
                # Подтверждение удаления
                if "confirm_delete_group" in st.session_state and st.session_state["confirm_delete_group"] == selected_group_id:
                    st.warning("Вы уверены, что хотите удалить группу? Это действие нельзя отменить.")
                    col1, col2 = st.columns(2)
                    with col1:
                        if st.button("Да, удалить", key="confirm_delete_group_yes"):
                            success, message = self.controller.delete_group(selected_group_id, tenant_id)
                            if success:
                                st.success(message)
                                # Очищаем состояние и перезагружаем страницу
                                del st.session_state["confirm_delete_group"]
                                # Перезагружаем страницу для обновления списка
                                st.rerun()
                            else:
                                st.error(message)
                    with col2:
                        if st.button("Отмена", key="confirm_delete_group_no"):
                            del st.session_state["confirm_delete_group"]
                            st.rerun()
                
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
                    st.subheader("Управление доступом к приложениям")
                    
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
                            key=f"app_access_app_select_{selected_group_id}"
                        )
                        
                        if selected_app:
                            app_type, app_id = selected_app.split(":")
                            
                            # Находим выбранное приложение
                            selected_app_obj = next((app for app in available_apps 
                                                if app.get('name') == app_type and app.get('id') == app_id), None)
                            
                            # Получаем текущие роли группы для этого приложения
                            current_roles = []
                            current_roles_original = []  # Для хранения оригинальных имен ролей с префиксом
                            for app_membership in selected_group.get('app_memberships', []):
                                if app_membership.get('app_type') == app_type and app_membership.get('app_id') == app_id:
                                    # Сохраняем оригинальное имя роли для последующего удаления
                                    role_original = app_membership.get('role', '')
                                    current_roles_original.append(role_original)
                                    
                                    # Нормализуем имя роли для отображения и сравнения с чекбоксами
                                    role = role_original
                                    if role.startswith('group_'):
                                        role = role[6:]  # Убираем 'group_'
                                    current_roles.append(role.lower())  # Приводим к нижнему регистру
                            
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
                            
                            # Показываем все роли, которые будут проверяться
                            role_values = [role["value"].lower() for role in all_roles]
                            
                            # Создаем форму с чекбоксами
                            with st.form(key=f"roles_form_{selected_group_id}_{app_type}_{app_id}"):
                                st.write("**Выберите роли для группы:**")
                                
                                # Используем чекбоксы для выбора ролей
                                selected_roles = []
                                for role in all_roles:
                                    # Проверяем, есть ли роль в текущих ролях (приводим обе к нижнему регистру)
                                    is_checked = role["value"].lower() in current_roles
                                    if st.checkbox(role["label"], value=is_checked, key=f"role_checkbox_{selected_group_id}_{app_type}_{app_id}_{role['value']}"):
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
                                        # (используем оригинальные имена ролей с префиксом group_)
                                        roles_to_remove = []
                                        for role_original in current_roles_original:
                                            role_norm = role_original.lower()
                                            if role_original.startswith('group_'):
                                                role_norm = role_original[6:].lower()  # Убираем 'group_' и приводим к нижнему регистру
                                            
                                            if role_norm not in selected_roles_norm:
                                                roles_to_remove.append(role_original)
                                        
                                        # Отладочная информация
                                        st.write(f"DEBUG: Текущие роли (нормализованные): {current_roles}")
                                        st.write(f"DEBUG: Выбранные роли (нормализованные): {selected_roles_norm}")
                                        st.write(f"DEBUG: Роли для добавления: {roles_to_add}")
                                        st.write(f"DEBUG: Роли для удаления: {roles_to_remove}")
                                        
                                        # Сначала добавляем новые роли
                                        if roles_to_add:
                                            success_count, failure_count, error_messages = self.controller.assign_multiple_roles_to_group(
                                                selected_group_id, app_type, app_id, roles_to_add, tenant_id
                                            )
                                            
                                            if failure_count > 0:
                                                st.warning(f"Не удалось добавить некоторые роли: {', '.join(error_messages)}")
                                        
                                        # Затем удаляем ненужные роли
                                        for role in roles_to_remove:
                                            success, message = self.controller.remove_group_from_app(
                                                selected_group_id, app_type, app_id, role, tenant_id
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
                st.warning("Группа не найдена") 