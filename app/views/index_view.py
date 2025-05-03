import streamlit as st
from .base_view import BaseView
from app.controllers import AppController, UserController, GroupController, RelationshipController

class IndexView(BaseView):
    """Представление для главной страницы."""
    
    def __init__(self):
        super().__init__()
        self.app_controller = AppController()
        self.user_controller = UserController()
        self.group_controller = GroupController()
        self.relationship_controller = RelationshipController()
    
    def render(self, skip_status_check=False):
        """Отображает главную страницу с обзором системы."""
        self.show_header("Система управления доступом Permify", 
                         "Управление приложениями, пользователями, группами и правами доступа")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("index_view")
        
        # Получаем общие статистические данные
        apps = self.app_controller.get_apps(tenant_id)
        users = self.user_controller.get_users(tenant_id)
        groups = self.group_controller.get_groups(tenant_id)
        success, relationships = self.relationship_controller.get_relationships(tenant_id)
        
        # Отображаем статистику в виде метрик
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Объектов", len([app for app in apps if not app.get('is_template', False)]))
        with col2:
            st.metric("Пользователей", len(users))
        with col3:
            st.metric("Групп", len(groups))
        with col4:
            if success and relationships:
                st.metric("Отношений", len(relationships.get("tuples", [])))
            else:
                st.metric("Отношений", "N/A")
        
        # Краткий обзор последних объектов
        st.subheader("Объекты")
        
        app_instances = [app for app in apps if not app.get('is_template', False)]
        if app_instances:
            # Отображаем только 5 последних объектов
            display_apps = app_instances[-5:]
            
            for app in display_apps:
                with st.container():
                    st.markdown(
                        f"""
                        <div style="
                            background-color: #1e2025;
                            padding: 15px;
                            border-radius: 5px;
                            margin-bottom: 10px;
                            border: 1px solid #4e5259;
                        ">
                            <h4 style="margin-top: 0; color: #e0e0e0;">{app.get('display_name')} (ID: {app.get('id')})</h4>
                            <p style="color: #e0e0e0;"><strong>Тип:</strong> {app.get('name')}</p>
                            <p style="color: #e0e0e0;"><strong>Пользователей:</strong> {len(app.get('users', []))}</p>
                            <p style="color: #e0e0e0;"><strong>Групп:</strong> {len(app.get('groups', []))}</p>
                            <p style="color: #e0e0e0;"><strong>Действий:</strong> {len(app.get('actions', []))}</p>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            
            if len(app_instances) > 5:
                st.info(f"Показаны 5 последних объектов из {len(app_instances)}. Перейдите в раздел 'Объекты' для просмотра всех.")
        else:
            st.info("В системе нет объектов. Создайте их в разделе 'Объекты'.")
        
        # Краткий обзор последних пользователей
        st.subheader("Последние пользователи")
        
        if users:
            # Отображаем только 5 последних пользователей
            display_users = users[-5:]
            
            # Создаем строку для каждого пользователя
            user_html = ""
            for user in display_users:
                user_html += f"""
                <div style="
                    display: inline-block;
                    background-color: #2d3035;
                    color: #e0e0e0;
                    padding: 10px 15px;
                    border-radius: 20px;
                    margin-right: 10px;
                    margin-bottom: 10px;
                    border: 1px solid #4e5259;
                ">
                    <span style="font-weight: bold;">👤 {user.get('name', 'Пользователь')}</span> (ID: {user.get('id', 'N/A')})
                </div>
                """
            
            st.markdown(f"<div>{user_html}</div>", unsafe_allow_html=True)
            
            if len(users) > 5:
                st.info(f"Показаны 5 последних пользователей из {len(users)}. Перейдите в раздел 'Пользователи' для просмотра всех.")
        else:
            st.info("В системе нет пользователей. Создайте их в разделе 'Пользователи'.")
        
        # Информация о проверке доступа
        st.subheader("Проверка доступа")
        
        st.markdown(
            """
            <div style="
                background-color: #1e2025;
                padding: 15px;
                border-radius: 5px;
                margin-bottom: 10px;
                border: 1px solid #4e5259;
                color: #e0e0e0;
            ">
                <h4 style="margin-top: 0; color: #e0e0e0;">Как проверить доступ?</h4>
                <p>1. Перейдите в раздел <strong>"Проверка доступа"</strong> или <strong>"Отношения"</strong></p>
                <p>2. Выберите пользователя, объект и действие</p>
                <p>3. Нажмите кнопку "Проверить доступ"</p>
                <p>4. Получите результат проверки и подробную информацию</p>
            </div>
            """,
            unsafe_allow_html=True
        )
        
        # Информация о системе
        st.sidebar.markdown("---")
        st.sidebar.markdown("### О системе")
        st.sidebar.markdown("**Permify GUI** - интерфейс для управления разрешениями в Permify")
        st.sidebar.markdown("Версия: 1.0.0")
        st.sidebar.markdown("Режим: Разработка") 