import streamlit as st
import pandas as pd
from .base_view import BaseView
from app.controllers import SchemaController, RelationshipController, UserController, GroupController, AppController, RedisController

class PermissionCheckView(BaseView):
    """Представление для проверки разрешений с современным дизайном."""
    
    def __init__(self):
        super().__init__()
        self.schema_controller = SchemaController()
        self.relationship_controller = RelationshipController()
        self.user_controller = UserController()
        self.group_controller = GroupController()
        self.app_controller = AppController()
        self.redis_controller = RedisController()
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс проверки разрешений."""
        self.show_header("Проверка доступа", "Проверка разрешений на действия над сущностями", icon="✅")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("permission_check_view")
        
        # Добавляем кнопку сброса кэша Redis
        col_cache1, col_cache2 = st.columns([3, 1])
        with col_cache2:
            if st.button("🔄 Сбросить кэш Redis", key="reset_redis_cache"):
                success, message = self.redis_controller.flush_cache()
                if success:
                    st.success(f"Кэш Redis успешно сброшен")
                else:
                    st.error(f"Ошибка при сбросе кэша: {message}")
        
        # Получаем список доступных схем
        schema_success, schema_result = self.schema_controller.get_current_schema(tenant_id)
        schema = schema_result.get("schema", {}) if schema_result else {}
        
        if schema_success:
            # Используем современную карточку для формы проверки
            st.markdown("""
            <div class="card">
                <div class="card-title">📋 Форма проверки разрешений</div>
                <div class="card-content">
                    <p>Заполните форму ниже для проверки прав доступа.</p>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("#### 📦 Сущность")
                
                entity_types = []
                if schema:
                    # Получаем все типы сущностей из схемы
                    try:
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
                st.markdown("#### 👤 Субъект")
                
                # Выбор типа субъекта
                subject_type = st.selectbox("Тип субъекта", ["user", "group"], key="perm_check_subject_type")
                subject_id = st.text_input("ID субъекта", "", key="perm_check_subject_id")
        
            with col3:
                st.markdown("#### 🔐 Разрешение")
        
                # Получаем разрешения для данного типа сущности
                permissions = []
                if schema and entity_type in entity_types:
                    try:
                        entity_def = schema.get("entity_definitions", {}).get(entity_type, {})
                        permission_defs = entity_def.get("permissions", {})
                        
                        permissions = list(permission_defs.keys())
                        
                        if permissions:
                            permission = st.selectbox("Разрешение", permissions, key="perm_check_permission")
                        else:
                            permission = st.text_input("Разрешение", "view", key="perm_check_permission_input")
                    except Exception as e:
                        st.warning(f"Не удалось получить разрешения: {str(e)}")
                        permission = st.text_input("Разрешение", "view", key="perm_check_permission_error")
                else:
                    permission = st.text_input("Разрешение", "view", key="perm_check_permission_manual")
                
                # Кнопка проверки с улучшенным UI
                st.markdown("<br>", unsafe_allow_html=True)  # Добавляем вертикальное пространство
                check_button = st.button("Проверить разрешение", key="check_permission_button", type="primary")
        
            # Проверка разрешения
            if check_button and subject_id and entity_id:
                st.markdown("#### Результат проверки")
                
                with st.spinner("Проверка разрешения..."):
                    success, result = self.relationship_controller.check_permission(
                        entity_type, entity_id, permission, subject_id, tenant_id)
                    
                    if success:
                        if result.get("can") == "CHECK_RESULT_ALLOWED":
                            # Используем компонент карточки для успешного результата
                            success_html = f"""
                            <div style="background-color: rgba(40, 167, 69, 0.1); border: 1px solid rgba(40, 167, 69, 0.5); color: var(--text); padding: 1rem; border-radius: var(--radius); margin: 1rem 0;">
                                <div style="display: flex; align-items: center;">
                                    <span style="font-size: 1.5rem; margin-right: 0.75rem;">✅</span>
                                    <div>
                                        <div style="font-weight: 600; font-size: 1.1rem;">Доступ разрешен</div>
                                        <div style="margin-top: 0.25rem; font-size: 0.9rem;">
                                            <code>{subject_type}:{subject_id}</code> имеет разрешение <code>{permission}</code> к <code>{entity_type}:{entity_id}</code>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """
                            st.markdown(success_html, unsafe_allow_html=True)
                        else:
                            # Используем компонент карточки для отрицательного результата
                            error_html = f"""
                            <div style="background-color: rgba(220, 53, 69, 0.1); border: 1px solid rgba(220, 53, 69, 0.5); color: var(--text); padding: 1rem; border-radius: var(--radius); margin: 1rem 0;">
                                <div style="display: flex; align-items: center;">
                                    <span style="font-size: 1.5rem; margin-right: 0.75rem;">❌</span>
                                    <div>
                                        <div style="font-weight: 600; font-size: 1.1rem;">Доступ запрещен</div>
                                        <div style="margin-top: 0.25rem; font-size: 0.9rem;">
                                            <code>{subject_type}:{subject_id}</code> не имеет разрешения <code>{permission}</code> к <code>{entity_type}:{entity_id}</code>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            """
                            st.markdown(error_html, unsafe_allow_html=True)
                        
                        # Показываем детали в улучшенном экспандере
                        with st.expander("Подробные данные ответа"):
                            # Показываем JSON с подсветкой
                            st.json(result)
                    else:
                        # Сообщение об ошибке с улучшенным форматированием
                        error_msg = f"""
                        <div style="background-color: rgba(220, 53, 69, 0.1); border: 1px solid rgba(220, 53, 69, 0.5); color: var(--text); padding: 1rem; border-radius: var(--radius); margin: 1rem 0;">
                            <div style="display: flex; align-items: center;">
                                <span style="font-size: 1.5rem; margin-right: 0.75rem;">❌</span>
                                <div>
                                    <div style="font-weight: 600; font-size: 1.1rem;">Ошибка при проверке</div>
                                    <div style="margin-top: 0.25rem; font-size: 0.9rem;">{result}</div>
                                </div>
                            </div>
                        </div>
                        """
                        st.markdown(error_msg, unsafe_allow_html=True)
        else:
            # Сообщение об ошибке схемы с улучшенным форматированием
            error_msg = f"""
            <div style="background-color: rgba(220, 53, 69, 0.1); border: 1px solid rgba(220, 53, 69, 0.5); color: var(--text); padding: 1rem; border-radius: var(--radius); margin: 1rem 0;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.5rem; margin-right: 0.75rem;">❌</span>
                    <div>
                        <div style="font-weight: 600; font-size: 1.1rem;">Ошибка схемы</div>
                        <div style="margin-top: 0.25rem; font-size: 0.9rem;">Не удалось получить схему: {schema_result}</div>
                    </div>
                </div>
            </div>
            """
            st.markdown(error_msg, unsafe_allow_html=True)
    
    def render_simplified(self, skip_status_check=False):
        """Отображает упрощенный интерфейс управления разрешениями с современным дизайном."""
        self.show_header("Управление разрешениями", 
                       "Простой интерфейс для проверки прав доступа пользователей", 
                       icon="✅")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("permission_check_view_simplified")
        
        # Добавляем кнопку сброса кэша Redis
        col_cache1, col_cache2 = st.columns([3, 1])
        with col_cache2:
            if st.button("🔄 Сбросить кэш Redis", key="reset_redis_cache_simplified"):
                success, message = self.redis_controller.flush_cache()
                if success:
                    st.success(f"Кэш Redis успешно сброшен")
                else:
                    st.error(f"Ошибка при сбросе кэша: {message}")
        
        # Получаем данные
        users = self.user_controller.get_users(tenant_id) or []
        groups = self.group_controller.get_groups(tenant_id) or []
        apps = self.app_controller.get_apps(tenant_id) or []
        
        # Только приложения с экземплярами, не шаблоны
        app_instances = [app for app in apps if not app.get('is_template', False) and app.get('id')]
        
        # Информационная карточка
        info_html = """
        <div style="background-color: rgba(23, 162, 184, 0.1); border: 1px solid rgba(23, 162, 184, 0.5); color: var(--text); padding: 1rem; border-radius: var(--radius); margin: 1rem 0;">
            <div style="display: flex; align-items: center;">
                <span style="font-size: 1.5rem; margin-right: 0.75rem;">ℹ️</span>
                <div>
                    <div style="font-weight: 600; font-size: 1.1rem;">Настройка прав доступа</div>
                    <div style="margin-top: 0.25rem; font-size: 0.9rem;">Управление правами доступа (назначение ролей, добавление в группы) доступно в разделе "Приложения".</div>
                </div>
            </div>
        </div>
        """
        st.markdown(info_html, unsafe_allow_html=True)
        
        # Карточка проверки доступа
        st.markdown("""
        <div class="card">
            <div class="card-title">📋 Проверка прав доступа пользователя</div>
            <div class="card-content">
                <p>Выберите пользователя, приложение и действие для проверки прав доступа.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### 👤 Пользователь")
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
            st.markdown("#### 📱 Приложение")
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
                st.info("Нет приложений. Создайте их в разделе 'Приложения'.")
                selected_app = None
        
        with col3:
            st.markdown("#### 🔑 Действие")
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
        
        # Центрированная кнопка проверки
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if selected_user and selected_app and selected_action:
                check_button = st.button("Проверить доступ", key="check_access_button", type="primary", use_container_width=True)
            else:
                st.button("Проверить доступ", key="check_access_disabled_button", type="primary", disabled=True, use_container_width=True)
        
        # Проверка доступа
        if selected_user and selected_app and selected_action and 'check_access_button' in st.session_state and st.session_state.check_access_button:
            st.markdown("#### Результат проверки")
            
            with st.spinner("Проверка прав доступа..."):
                success, result = self.relationship_controller.check_permission(
                    selected_app['name'], selected_app['id'], selected_action, selected_user, tenant_id
                )
                
                if success:
                    # Правильно определяем значение can_access
                    can_access = False
                    
                    if isinstance(result, dict):
                        # Проверяем все возможные варианты значения can
                        if "can" in result:
                            if isinstance(result["can"], bool):
                                can_access = result["can"]
                            elif isinstance(result["can"], str):
                                can_access = result["can"] == "CHECK_RESULT_ALLOWED" or result["can"] == "true" or result["can"] == "True"
                    
                    # Выводим результат с улучшенным форматированием
                    if can_access:
                        # Используем компонент карточки для успешного результата
                        success_html = f"""
                        <div style="background-color: rgba(40, 167, 69, 0.1); border: 1px solid rgba(40, 167, 69, 0.5); color: var(--text); padding: 1rem; border-radius: var(--radius); margin: 1rem 0;">
                            <div style="display: flex; align-items: center;">
                                <span style="font-size: 1.5rem; margin-right: 0.75rem;">✅</span>
                                <div>
                                    <div style="font-weight: 600; font-size: 1.1rem;">Доступ разрешен</div>
                                    <div style="margin-top: 0.25rem; font-size: 0.9rem;">
                                        Пользователь имеет разрешение на действие <code>{selected_action}</code> для приложения <code>{selected_app.get('display_name')}</code>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """
                        st.markdown(success_html, unsafe_allow_html=True)
                    else:
                        # Используем компонент карточки для отрицательного результата
                        error_html = f"""
                        <div style="background-color: rgba(220, 53, 69, 0.1); border: 1px solid rgba(220, 53, 69, 0.5); color: var(--text); padding: 1rem; border-radius: var(--radius); margin: 1rem 0;">
                            <div style="display: flex; align-items: center;">
                                <span style="font-size: 1.5rem; margin-right: 0.75rem;">❌</span>
                                <div>
                                    <div style="font-weight: 600; font-size: 1.1rem;">Доступ запрещен</div>
                                    <div style="margin-top: 0.25rem; font-size: 0.9rem;">
                                        Пользователь не имеет разрешения на действие <code>{selected_action}</code> для приложения <code>{selected_app.get('display_name')}</code>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """
                        st.markdown(error_html, unsafe_allow_html=True)
                    
                    # Показываем детальную информацию в экспандере
                    if isinstance(result, dict):
                        with st.expander("Детальная информация"):
                            # Очищаем ненужные данные о local development mode
                            if "metadata" in result and "reason" in result["metadata"] and "Local development mode" in result["metadata"]["reason"]:
                                result["metadata"]["reason"] = "Проверка разрешений"
                            
                            # Отображаем данные в формате JSON
                            st.json(result) 