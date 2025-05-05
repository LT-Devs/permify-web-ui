import streamlit as st
import time
from .base_view import BaseView
from app.controllers import AppController, RelationshipController, UserController, SchemaController

class IndexView(BaseView):
    """Представление для главной страницы."""
    
    def __init__(self):
        super().__init__()
        self.app_controller = AppController()
        self.relationship_controller = RelationshipController()
        self.user_controller = UserController()
        self.schema_controller = SchemaController()
    
    def render(self, skip_status_check=False):
        """Отображает главную страницу."""
        self.show_header("Обзор системы", 
                         "Обзор системы разрешений, пользователей, групп и приложений")
        
        # Проверка статуса
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("index_view")
        
        # Получаем данные
        apps = self.app_controller.get_apps(tenant_id)
        users = self.user_controller.get_users(tenant_id)
        success, schema_result = self.schema_controller.get_current_schema(tenant_id)
        
        # Колонки для метрик
        metrics_cols = st.columns(4)
        
        # Подсчет метрик
        total_apps = sum(1 for app in apps if not app.get('is_template', False))
        total_users = len(users)
        total_relationships = 0
        total_entities = 0
        
        # Загружаем отношения
        success, relationships = self.relationship_controller.get_relationships(tenant_id)
        if success:
            total_relationships = len(relationships.get('tuples', []))
        
        # Загружаем сущности
        if success and schema_result:
            schema_entities = self.schema_controller.extract_entities_info(schema_result)
            total_entities = len(schema_entities)
        
        # Метрики в колонках
        with metrics_cols[0]:
            st.metric("Приложения", total_apps)
        
        with metrics_cols[1]:
            st.metric("Пользователи", total_users)
            
        with metrics_cols[2]:
            st.metric("Отношения", total_relationships)
            
        with metrics_cols[3]:
            st.metric("Сущности", total_entities)
        
        # Разделитель
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Фильтруем только экземпляры приложений (не шаблоны)
        app_instances = [app for app in apps if not app.get('is_template', False)]
        
        # Последние приложения
        st.subheader("📱 Последние приложения")
        
        # Отображаем карточки приложений в виде колонок для лучшего представления
        if app_instances:
            # Определяем количество колонок в зависимости от числа приложений
            num_apps = min(len(app_instances), 5)  # Максимум 5 приложений
            cols = st.columns(min(num_apps, 3))  # Максимум 3 колонки
            
            # Распределяем приложения по колонкам
            for i, app in enumerate(app_instances[:5]):
                col_idx = i % len(cols)
                with cols[col_idx]:
                    app_name = app.get('display_name', app.get('name', 'Неизвестное приложение'))
                    app_type = app.get('name', 'unknown')
                    app_id = app.get('id', '0')
                    users_count = len(app.get('users', {}))
                    groups_count = len(app.get('groups', {}))
                    actions_count = len(app.get('actions', []))
                    
                    # Используем встроенные компоненты Streamlit вместо HTML
                    st.markdown(f"**📱 {app_name}**")
                    st.caption(f"Тип: {app_type}")
                    st.caption(f"Пользователей: {users_count}")
                    st.caption(f"Групп: {groups_count}")
                    st.caption(f"Действий: {actions_count}")
                    st.caption(f"ID: {app_id}")
                    # Добавляем разделитель между картами
                    st.markdown("---")
        else:
            st.info("Нет приложений. Создайте свое первое приложение во вкладке 'Приложения'.")
        
        # Разделитель
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Последние пользователи
        st.subheader("👤 Последние пользователи")
        
        # Обрабатываем users как словарь или список в зависимости от его типа
        user_items = []
        if isinstance(users, dict):
            user_items = list(users.items())[:5]  # Берем первые 5 элементов
        else:
            user_items = [(user.get('id', 'unknown'), user) for user in users[:5]]
        
        if user_items:
            # Создаем колонки для пользователей
            num_users = len(user_items)
            user_cols = st.columns(min(num_users, 5))  # Максимум 5 колонок
            
            for i, (user_id, user_info) in enumerate(user_items):
                with user_cols[i]:
                    user_name = user_info.get('display_name', user_id)
                    st.markdown(f"**👤 {user_name}**")
        else:
            st.info("Нет пользователей. Создайте своего первого пользователя во вкладке 'Пользователи'.")
        
        # Разделитель
        st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
        
        # Проверка доступа
        st.subheader("✅ Проверка доступа")
        
        st.markdown("""
        ### ❓ Как проверить доступ?
        
        1. Перейдите на вкладку "Проверка доступа" в меню слева
        2. Выберите приложение, пользователя и действие
        3. Нажмите кнопку "Проверить доступ"
        
        Или используйте вкладку "Интеграция" для получения примеров кода интеграции Permify с вашим приложением.
        """)
    
    def about(self):
        """Отображает информацию о приложении."""
        with st.sidebar:
            st.subheader("О приложении")
            st.markdown("Permify GUI - интерфейс для управления системой доступа Permify")
            st.sidebar.markdown("Версия: 2.0.2a")
            st.sidebar.markdown("Разработчик: BadKiko (LT-Devs)") 