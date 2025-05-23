import streamlit as st
import os
from dotenv import load_dotenv

# Настройка страницы Streamlit
st.set_page_config(
    page_title="Permify GUI", 
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/permify/permify',
        'Report a bug': 'https://github.com/permify/permify/issues',
        'About': 'Permify GUI - интерфейс управления системой доступа'
    }
)

# Загружаем переменные из .env файла
load_dotenv()

# Константы
DEFAULT_TENANT = os.environ.get("PERMIFY_TENANT", "t1")

# Импорт представлений
from app.views import (
    IndexView, SchemaView, PermissionCheckView, TenantView,
    RelationshipView, UserView, GroupView, AppView, IntegrationView,
    CacheView
)
from app.controllers import BaseController, RedisController, AppController, RelationshipController
from app.views.styles import get_modern_styles

# Применяем современные стили
st.markdown(get_modern_styles(), unsafe_allow_html=True)

def check_permify_status():
    """Проверяет статус подключения к Permify."""
    controller = BaseController()
    status, message = controller.check_permify_status()
    if status:
        st.sidebar.success("✅ Permify доступен")
    else:
        st.sidebar.error(f"❌ Permify недоступен: {message}")
    
    return status

def main():
    # Инициализируем сессию
    if 'tenant_id' not in st.session_state:
        st.session_state.tenant_id = DEFAULT_TENANT
    
    # Создаем боковое меню с улучшенным дизайном
    with st.sidebar:
        st.title("🔐 Permify")
        st.caption("Управление системой доступа")
        
        # Разделитель с красивым оформлением
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Раздел "Tenant" с современным оформлением
        st.markdown("#### Настройки tenant")
        tenant_id = st.text_input(
            "ID tenant",
            value=st.session_state.get('tenant_id', DEFAULT_TENANT),
            help="Идентификатор tenant в Permify",
            key="tenant_id_input"
        )
        
        # Обновляем ID tenant в сессии
        if tenant_id != st.session_state.get('tenant_id'):
            st.session_state.tenant_id = tenant_id
        
        # Проверяем статус Permify
        check_permify_status()
        
        # Разделитель с красивым оформлением
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        
        # Навигация с иконками и современным дизайном
        st.markdown("#### Навигация")
        
        # Список страниц с иконками
        pages = [
            {"id": "home", "icon": "🏠", "name": "Обзор", "description": "Обзор системы"},
            {"id": "apps", "icon": "📱", "name": "Приложения", "description": "Управление приложениями и правами доступа"},
            {"id": "users", "icon": "👤", "name": "Пользователи", "description": "Управление пользователями"},
            {"id": "groups", "icon": "👥", "name": "Группы", "description": "Управление группами пользователей"},
            {"id": "relationships", "icon": "🔗", "name": "Отношения", "description": "Управление отношениями между объектами"},
            {"id": "check", "icon": "✅", "name": "Проверка доступа", "description": "Проверка прав доступа пользователей к объектам"},
            {"id": "schemas", "icon": "📝", "name": "Схемы", "description": "Управление схемами доступа"},
            {"id": "tenants", "icon": "🏢", "name": "Tenants", "description": "Управление tenants"},
            {"id": "integration", "icon": "🔄", "name": "Интеграция", "description": "Управление интеграцией"},
            {"id": "cache", "icon": "🗑️", "name": "Управление кэшем", "description": "Управление Redis-кэшем"}
        ]
        
        # Современные кнопки навигации с использованием st.button
        page = None
        for item in pages:
            button_label = f"{item['icon']} {item['name']}"
            if st.button(button_label, help=item["description"], key=f"nav_{item['id']}"):
                page = item["id"]
                st.session_state.page = page
        
        # Используем сохраненный выбор, если текущий не определен
        if page is None and "page" in st.session_state:
            page = st.session_state.page
        elif page is None:
            page = "home"
            
        # Подвал (footer) с информацией о системе
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
        st.markdown("""
        <div style="color: var(--text-secondary); font-size: 0.8rem; padding: 0.5rem 0;">
            <p><strong>Permify GUI</strong> версия 2.0.1a</p>
            <p>© 2023 BadKiko (LT-Devs)</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Отображаем выбранную страницу с контейнером
    with st.container():
        if page == "home":
            IndexView().render()
        elif page == "apps":
            AppView().render()
        elif page == "users":
            UserView().render()
        elif page == "groups":
            GroupView().render()
        elif page == "relationships":
            RelationshipView().render()
        elif page == "schemas":
            SchemaView().render()
        elif page == "check":
            PermissionCheckView().render_simplified()
        elif page == "tenants":
            TenantView().render()
        elif page == "integration":
            IntegrationView().render()
        elif page == "cache":
            CacheView().render()

# Запуск приложения
if __name__ == "__main__":
    main() 