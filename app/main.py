import streamlit as st
import os
from app.views import (
    UserView, 
    GroupView, 
    AppView, 
    SchemaView, 
    RelationshipView,
    PermissionCheckView,
    StatusView
)
from app.controllers import BaseController

def setup_page():
    """Настраивает страницу Streamlit."""
    st.set_page_config(
        page_title="Permify API Manager",
        page_icon="🔒",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    
    # Добавляем стили CSS
    st.markdown("""
    <style>
    .main .block-container {
        padding-top: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        border-radius: 4px;
        padding: 10px 16px;
        background-color: #f0f2f6;
        font-weight: 500;
        color: #31333F;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4257b2 !important;
        color: white !important;
        font-weight: 600;
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #dfe1e6;
        color: #0F1116;
        cursor: pointer;
    }
    .stTabs [aria-selected="true"]:hover {
        background-color: #3a4c9f !important;
        color: white !important;
    }
    /* Скрываем дублирующиеся элементы статуса Permify */
    .sidebar .element-container:has(.stSuccess:contains("Permify доступен")) ~ .element-container:has(.stSuccess:contains("Permify доступен")) {
        display: none;
    }
    .sidebar .element-container:has(.stError:contains("Permify недоступен")) ~ .element-container:has(.stError:contains("Permify недоступен")) {
        display: none;
    }
    /* Скрываем дублирующиеся поля ID арендатора */
    .sidebar .element-container:has(label:contains("ID арендатора")) ~ .element-container:has(label:contains("ID арендатора")) {
        display: none;
    }
    </style>
    """, unsafe_allow_html=True)

def check_permify_status():
    """Проверяет статус подключения к Permify."""
    controller = BaseController()
    status, message = controller.check_permify_status()
    if status:
        st.sidebar.success("✅ Permify доступен")
    else:
        st.sidebar.error(f"❌ Permify недоступен: {message}")
    
    return status

def get_mode():
    """Получает текущий режим работы из боковой панели и настраивает общие параметры."""
    st.sidebar.title("Permify API Manager")
    
    mode = st.sidebar.radio(
        "Выберите режим работы",
        ["Упрощенный", "Ручной"],
        index=0,
        help="Упрощенный режим для администраторов, ручной режим для разработчиков"
    )
    
    # Единое поле для ID арендатора, которое будет использоваться во всех представлениях
    if 'tenant_id' not in st.session_state:
        st.session_state.tenant_id = "t1"
    
    st.session_state.tenant_id = st.sidebar.text_input(
        "ID арендатора", 
        value=st.session_state.tenant_id, 
        key="global_tenant_id"
    )
    
    # Проверяем статус Permify один раз
    permify_status = check_permify_status()
    st.session_state.permify_status = permify_status
    
    st.sidebar.markdown("---")
    return mode

def display_simplified_mode():
    """Отображает интерфейс в упрощенном режиме."""
    st.markdown("# Permify API Manager - Упрощенный режим")
    st.markdown("Управление пользователями, группами и приложениями в Permify")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Пользователи", "Группы", "Приложения", "Статус системы"])
    
    # Если Permify недоступен, показываем сообщение
    if not st.session_state.get('permify_status', False):
        for tab in [tab1, tab2, tab3]:
            with tab:
                st.error("❌ Permify недоступен. Проверьте подключение к серверу.")
        with tab4:
            status_view = StatusView()
            status_view.render(skip_status_check=True)
        return
    
    with tab1:
        user_view = UserView()
        user_view.render(skip_status_check=True)
    
    with tab2:
        group_view = GroupView()
        group_view.render(skip_status_check=True)
    
    with tab3:
        app_view = AppView()
        app_view.render(skip_status_check=True)
    
    with tab4:
        status_view = StatusView()
        status_view.render(skip_status_check=True)

def display_manual_mode():
    """Отображает интерфейс в ручном режиме."""
    st.markdown("# Permify API Manager - Ручной режим")
    st.markdown("Управление схемами, отношениями и разрешениями в Permify")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Схемы", "Отношения", "Проверка доступа", "Статус системы"])
    
    # Если Permify недоступен, показываем сообщение
    if not st.session_state.get('permify_status', False):
        for tab in [tab1, tab2, tab3]:
            with tab:
                st.error("❌ Permify недоступен. Проверьте подключение к серверу.")
        with tab4:
            status_view = StatusView()
            status_view.render(skip_status_check=True)
        return
    
    with tab1:
        schema_view = SchemaView()
        schema_view.render(skip_status_check=True)
    
    with tab2:
        relationship_view = RelationshipView()
        relationship_view.render(skip_status_check=True)
    
    with tab3:
        permission_check_view = PermissionCheckView()
        permission_check_view.render(skip_status_check=True)
    
    with tab4:
        status_view = StatusView()
        status_view.render(skip_status_check=True)

def main():
    """Основная функция приложения."""
    setup_page()
    
    mode = get_mode()
    
    if mode == "Упрощенный":
        display_simplified_mode()
    else:
        display_manual_mode()

if __name__ == "__main__":
    main() 