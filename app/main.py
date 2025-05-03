import streamlit as st
import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Константы
DEFAULT_TENANT = os.environ.get("PERMIFY_TENANT", "t1")

# Импорт представлений
from app.views import (
    IndexView, SchemaView, PermissionCheckView, TenantView,
    RelationshipView, UserView, GroupView, AppView
)
from app.controllers import BaseController

# Настройка Streamlit
st.set_page_config(
    page_title="Permify GUI",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    # Создаем боковое меню
    with st.sidebar:
        st.title("Permify GUI")
        st.caption("Упрощенный интерфейс управления")
        
        # Раздел "Арендатор" (Tenant)
        tenant_id = st.text_input(
            "ID арендатора (tenant)",
            value=st.session_state.get('tenant_id', DEFAULT_TENANT),
            help="Идентификатор арендатора в Permify",
            key="tenant_id_input"
        )
        
        # Обновляем ID арендатора в сессии
        if tenant_id != st.session_state.get('tenant_id'):
            st.session_state.tenant_id = tenant_id
        
        # Проверяем статус Permify
        check_permify_status()
        
        # Навигация
        st.header("Навигация")
        
        # Список страниц с иконками и описаниями
        pages = [
            {"id": "home", "name": "🏠 Главная", "description": "Обзор системы"},
            {"id": "apps", "name": "📱 Объекты", "description": "Управление объектами и правами доступа"},
            {"id": "users", "name": "👤 Пользователи", "description": "Управление пользователями"},
            {"id": "groups", "name": "👥 Группы", "description": "Управление группами пользователей"},
            {"id": "relationships", "name": "🔗 Отношения", "description": "Управление отношениями между объектами"},
            {"id": "check", "name": "✅ Проверка доступа", "description": "Проверка прав доступа пользователей к объектам"},
            {"id": "schemas", "name": "📝 Схемы", "description": "Управление схемами доступа"},
            {"id": "tenants", "name": "🏢 Арендаторы", "description": "Управление арендаторами"}
        ]
        
        # Виджет для выбора страницы
        page = None
        for item in pages:
            if st.button(item["name"], help=item["description"], key=f"nav_{item['id']}"):
                page = item["id"]
                st.session_state.page = page
        
        # Используем сохраненный выбор, если текущий не определен
        if page is None and "page" in st.session_state:
            page = st.session_state.page
        elif page is None:
            page = "home"
    
    # Отображаем выбранную страницу
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

# Запуск приложения
if __name__ == "__main__":
    main() 