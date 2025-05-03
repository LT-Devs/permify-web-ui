import streamlit as st
import pandas as pd
from .base_view import BaseView
from app.controllers import SchemaController, RelationshipController, UserController, GroupController, AppController

class PermissionCheckView(BaseView):
    """Представление для проверки разрешений."""
    
    def __init__(self):
        super().__init__()
        self.schema_controller = SchemaController()
        self.relationship_controller = RelationshipController()
        self.user_controller = UserController()
        self.group_controller = GroupController()
        self.app_controller = AppController()
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс проверки разрешений."""
        self.show_header("Проверка доступа", "Проверка разрешений на действия над сущностями")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("permission_check_view")
        
        # Получаем список доступных схем
        schema_success, schema_result = self.schema_controller.get_current_schema(tenant_id)
        
        if schema_success:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.subheader("Сущность")
                
                entity_types = []
                if schema_result:
                    # Получаем все типы сущностей из схемы
                    try:
                        schema = schema_result.get("schema", {})
                        entity_definitions = schema.get("entity_definitions", {})
                        
                        entity_types = list(entity_definitions.keys())
                        
                        # Выбор типа сущности
                        entity_type = st.selectbox("Тип сущности", entity_types, index=entity_types.index("petitions") if "petitions" in entity_types else 0)
                    except Exception as e:
                        st.warning(f"Не удалось получить типы сущностей из схемы: {str(e)}")
                        entity_type = st.text_input("Тип сущности", "petitions", key="perm_check_entity_type_input")
                else:
                        entity_type = st.text_input("Тип сущности", "petitions", key="perm_check_entity_type_manual")

                entity_id = st.text_input("ID сущности", "1", key="perm_check_entity_id")
            
            with col2:
                st.subheader("Субъект")
                
                # Выбор типа субъекта
                subject_type = st.selectbox("Тип субъекта", ["user", "group"], key="perm_check_subject_type")
                subject_id = st.text_input("ID субъекта", "", key="perm_check_subject_id")
        
            with col3:
                st.subheader("Проверка")
        
                # Получаем разрешения для данного типа сущности
                permissions = []
                if schema_success and entity_type in entity_types:
                    try:
                        entity_def = schema.get("entity_definitions", {}).get(entity_type, {})
                        permission_defs = entity_def.get("permissions", {})
                        
                        permissions = list(permission_defs.keys())
                    except Exception as e:
                        st.warning(f"Не удалось получить разрешения: {str(e)}")
                
                        if permissions:
                            permission = st.selectbox("Разрешение", permissions, key="perm_check_permission")
                else:
                    permission = st.text_input("Разрешение", "view", key="perm_check_permission_input")
                
                # Кнопка проверки
                check_button = st.button("Проверить разрешение", key="check_permission_button")
        
            # Проверка разрешения
            if check_button and subject_id and entity_id:
                st.subheader("Результат проверки")
                
                with st.spinner("Проверка разрешения..."):
                    success, result = self.relationship_controller.check_permission(
                        entity_type, entity_id, permission, subject_id, tenant_id)
                    
                    if success:
                        if result.get("can") == "CHECK_RESULT_ALLOWED":
                            st.success(f"✅ Разрешение: {subject_type}:{subject_id} имеет доступ к {entity_type}:{entity_id}:{permission}")
                        else:
                            st.error(f"❌ Отказано: {subject_type}:{subject_id} не имеет доступа к {entity_type}:{entity_id}:{permission}")
                        
                        # Показываем детали
                        with st.expander("Подробные данные ответа"):
                            st.json(result)
                    else:
                        st.error(f"Ошибка при проверке разрешения: {result}")
        else:
            st.error(f"Не удалось получить схему: {schema_result}")
    
    def render_simplified(self, skip_status_check=False):
        """Отображает упрощенный интерфейс управления разрешениями."""
        self.show_header("Управление разрешениями", 
                       "Простой интерфейс для проверки и визуализации прав доступа")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("permission_check_view_simplified")
        
        # Получаем данные
        users = self.user_controller.get_users(tenant_id)
        groups = self.group_controller.get_groups(tenant_id)
        apps = self.app_controller.get_apps(tenant_id)
        
        # Только приложения с экземплярами, не шаблоны
        app_instances = [app for app in apps if not app.get('is_template', False) and app.get('id')]
        
        # Удаляем дублирующуюся функциональность "Матрица доступа"
        # и сосредотачиваемся только на проверке доступа
        st.subheader("Проверка прав доступа пользователя")
        
        # Добавляем информационное сообщение
        st.info("⚠️ Управление правами доступа (назначение ролей, добавление групп) доступно в разделе 'Объекты'")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Выбор пользователя
            if users:
                selected_user = st.selectbox(
                    "Выберите пользователя",
                    [user.get('id') for user in users],
                    format_func=lambda x: next((user.get('name', f"Пользователь {user.get('id')}") 
                                              for user in users if user.get('id') == x), x),
                    key="check_user"
                )
            else:
                st.info("Нет пользователей. Создайте пользователей в разделе 'Пользователи'.")
                selected_user = st.text_input("ID пользователя", "", key="check_user_manual")
        
        with col2:
            # Выбор приложения
            if app_instances:
                app_options = [(i, app) for i, app in enumerate(app_instances)]
                selected_app_index = st.selectbox(
                    "Выберите приложение",
                    range(len(app_options)),
                    format_func=lambda i: f"{app_options[i][1].get('display_name')} (ID: {app_options[i][1].get('id')})",
                    key="check_app"
                )
                selected_app = app_options[selected_app_index][1]
            else:
                st.info("Нет приложений. Создайте приложения в разделе 'Приложения'.")
                selected_app = None
        
        with col3:
            # Выбор действия
            if selected_app and selected_app.get('actions'):
                selected_action = st.selectbox(
                    "Выберите действие",
                    [action.get('name') for action in selected_app.get('actions')],
                    key="check_action"
                )
            else:
                st.info("У выбранного приложения нет действий.")
                selected_action = st.text_input("Действие", "", key="check_action_manual")
        
        # Кнопка проверки
        if selected_user and selected_app and selected_action:
            if st.button("Проверить доступ", type="primary", key="check_access_button"):
                with st.spinner("Проверка доступа..."):
                    success, result = self.app_controller.check_user_permission(
                        selected_app.get('name'),
                        selected_app.get('id'),
                        selected_user,
                        selected_action,
                        tenant_id
                    )
                    
                    if success:
                        if result.get("can") == "CHECK_RESULT_ALLOWED":
                            st.success(f"✅ Пользователь имеет разрешение на действие '{selected_action}'")
                        else:
                            st.error(f"❌ Пользователь не имеет разрешения на действие '{selected_action}'")
                        
                        # Показываем детали
                        with st.expander("Подробная информация"):
                            st.json(result)
                    else:
                        st.error(f"Ошибка при проверке разрешения: {result}")
                    
        # Показываем дополнительную информацию о пользователе и его ролях
        if selected_user and selected_app:
            st.subheader("Информация о пользователе и его ролях")
            
            # Проверяем, имеет ли пользователь роли в этом приложении
            user_roles = [user_role for user_role in selected_app.get('users', []) 
                        if user_role.get('user_id') == selected_user]
            
            if user_roles:
                roles_data = []
                for user_role in user_roles:
                    role = user_role.get('role')
                    roles_data.append({
                        "Роль": {"owner": "Владелец", "editor": "Редактор", "viewer": "Просмотрщик"}.get(role, role)
                    })
                
                st.dataframe(
                    pd.DataFrame(roles_data),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Пользователь не имеет ролей в этом приложении")
                
            # Проверяем, входит ли пользователь в группы с доступом к приложению
            user_groups = []
            for group in groups:
                if selected_user in group.get('members', []) and group.get('id') in selected_app.get('groups', []):
                    user_groups.append({
                        "Группа": group.get('name', f"Группа {group.get('id')}"),
                        "ID": group.get('id')
                    })
            
            if user_groups:
                st.subheader("Группы пользователя с доступом к объекту")
                st.dataframe(
                    pd.DataFrame(user_groups),
                    use_container_width=True,
                    hide_index=True
                ) 