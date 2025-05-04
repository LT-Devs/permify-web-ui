import streamlit as st
from .base_view import BaseView
from app.controllers import AppController, UserController, GroupController, RelationshipController

class IndexView(BaseView):
    """Представление для главной страницы с улучшенным дизайном."""
    
    def __init__(self):
        super().__init__()
        self.app_controller = AppController()
        self.user_controller = UserController()
        self.group_controller = GroupController()
        self.relationship_controller = RelationshipController()
    
    def render(self, skip_status_check=False):
        """Отображает главную страницу с обзором системы."""
        self.show_header(
            "Система управления доступом", 
            "Мониторинг и управление разрешениями для приложений и пользователей",
            icon="🔐"
        )
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("index_view")
        
        # Получаем общие статистические данные
        apps = self.app_controller.get_apps(tenant_id)
        users = self.user_controller.get_users(tenant_id)
        groups = self.group_controller.get_groups(tenant_id)
        success, relationships = self.relationship_controller.get_relationships(tenant_id)
        
        # Отображаем статистику в виде улучшенных метрик
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            metric_html = self.render_metric(
                "Приложения", 
                len([app for app in apps if not app.get('is_template', False)]),
                "Активные приложения в системе"
            )
            st.markdown(metric_html, unsafe_allow_html=True)
            
        with col2:
            metric_html = self.render_metric(
                "Пользователи", 
                len(users),
                "Зарегистрированные пользователи"
            )
            st.markdown(metric_html, unsafe_allow_html=True)
            
        with col3:
            metric_html = self.render_metric(
                "Группы", 
                len(groups),
                "Группы пользователей"
            )
            st.markdown(metric_html, unsafe_allow_html=True)
            
        with col4:
            if success and relationships:
                rel_count = len(relationships.get("tuples", []))
                metric_html = self.render_metric(
                    "Отношения", 
                    rel_count,
                    "Связи между объектами"
                )
            else:
                metric_html = self.render_metric(
                    "Отношения", 
                    "N/A",
                    "Связи между объектами"
                )
            st.markdown(metric_html, unsafe_allow_html=True)
        
        # Добавляем разделитель
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Используем две колонки для отображения контента
        col_left, col_right = st.columns([2, 1])
        
        # Краткий обзор последних объектов в левой колонке
        with col_left:
            st.subheader("📱 Последние приложения")
            
            app_instances = [app for app in apps if not app.get('is_template', False)]
            if app_instances:
                # Отображаем только 5 последних объектов с современным дизайном
                display_apps = app_instances[-5:]
                
                for app in display_apps:
                    app_type = app.get('name', 'N/A')
                    users_count = len(app.get('users', []))
                    groups_count = len(app.get('groups', []))
                    actions_count = len(app.get('actions', []))
                    
                    app_content = f"""
                    <div>
                        <strong>Тип:</strong> {app_type}<br>
                        <strong>Пользователей:</strong> {users_count}<br>
                        <strong>Групп:</strong> {groups_count}<br>
                        <strong>Действий:</strong> {actions_count}
                    </div>
                    """
                    
                    self.render_card(
                        f"{app.get('display_name')}",
                        app_content,
                        icon="📱",
                        footer=f"ID: {app.get('id')}"
                    )
                
                if len(app_instances) > 5:
                    st.info(f"Показаны 5 последних приложений из {len(app_instances)}. Перейдите в раздел 'Приложения' для просмотра всех.")
            else:
                st.info("В системе нет приложений. Создайте их в разделе 'Приложения'.")
        
        # Краткий обзор последних пользователей и инструкции в правой колонке
        with col_right:
            st.subheader("👤 Последние пользователи")
            
            if users:
                # Отображаем только 5 последних пользователей
                display_users = users[-5:]
                
                # Создаем строку для каждого пользователя
                user_html = "<div style='margin-bottom: 1rem;'>"
                for user in display_users:
                    user_html += f"""
                    <div style="
                        background-color: var(--secondary-bg);
                        color: var(--text);
                        padding: 0.5rem 0.75rem;
                        border-radius: 1rem;
                        margin-right: 0.5rem;
                        margin-bottom: 0.5rem;
                        border: 1px solid var(--border);
                        display: inline-block;
                        font-size: 0.9rem;
                    ">
                        <span style="font-weight: 500;">👤 {user.get('name', 'Пользователь')}</span>
                    </div>
                    """
                user_html += "</div>"
                
                st.markdown(user_html, unsafe_allow_html=True)
                
                if len(users) > 5:
                    st.info(f"Показаны 5 последних пользователей из {len(users)}. Перейдите в раздел 'Пользователи' для просмотра всех.")
            else:
                st.info("В системе нет пользователей. Создайте их в разделе 'Пользователи'.")
                
            # Добавляем разделитель
            st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
            
            # Информация о проверке доступа
            st.subheader("✅ Проверка доступа")
            
            help_content = """
            <ol style="padding-left: 1.5rem;">
                <li>Перейдите в раздел <strong>"Проверка доступа"</strong></li>
                <li>Выберите пользователя, приложение и действие</li>
                <li>Нажмите кнопку "Проверить доступ"</li>
                <li>Получите результат проверки</li>
            </ol>
            """
            
            self.render_card(
                "Как проверить доступ?",
                help_content,
                icon="❓"
            )
        
        # Информация о системе
        st.sidebar.markdown("---")
        st.sidebar.markdown("### О системе")
        st.sidebar.markdown("**Permify GUI** - интерфейс для управления разрешениями в Permify")
        st.sidebar.markdown("Версия: 2.0.1a")
        st.sidebar.markdown("Разработчик: BadKiko (LT-Devs)") 