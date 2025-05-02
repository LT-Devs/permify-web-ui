import streamlit as st
from app.controllers import BaseController

class BaseView:
    """Базовый класс для всех представлений."""
    
    def __init__(self):
        self.controller = BaseController()
    
    def show_header(self, title, description=None):
        """Отображает заголовок страницы."""
        st.title(title)
        if description:
            st.write(description)
    
    def show_status(self):
        """Отображает статус подключения к Permify."""
        status, message = self.controller.check_permify_status()
        if status:
            st.sidebar.success("✅ Permify доступен")
        else:
            st.sidebar.error(f"❌ Permify недоступен: {message}")
        
        return status
    
    def get_tenant_id(self, view_name="default"):
        """Получает ID арендатора из session_state."""
        # Используем глобальное значение, которое установлено в main.py
        if 'tenant_id' in st.session_state:
            return st.session_state.tenant_id
        else:
            # Запасной вариант, если по какой-то причине глобальное значение не установлено
            return "t1"
    
    def render(self, skip_status_check=False):
        """Метод для переопределения в дочерних классах."""
        raise NotImplementedError("Метод render должен быть реализован в дочернем классе.") 