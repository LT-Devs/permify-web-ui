import streamlit as st
from app.controllers import BaseController
from app.views.styles import get_modern_styles

class BaseView:
    """Базовый класс для всех представлений с современным дизайном."""
    
    def __init__(self):
        self.controller = BaseController()
        # Убедимся, что стили загружены
        if 'styles_loaded' not in st.session_state:
            st.markdown(get_modern_styles(), unsafe_allow_html=True)
            st.session_state.styles_loaded = True
    
    def show_header(self, title, description=None, icon=None):
        """Отображает современный заголовок страницы с иконкой."""
        if icon:
            title = f"{icon} {title}"
        
        st.markdown(f"## {title}")
        
        if description:
            st.markdown(f"<p style='color: var(--text-secondary); font-size: 1rem; margin-bottom: 1.5rem;'>{description}</p>", unsafe_allow_html=True)
        
        # Добавляем разделитель после заголовка
        st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
    
    def show_status(self):
        """Отображает красивый индикатор статуса подключения к Permify."""
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
    
    def render_card(self, title, content, icon=None, color="primary", footer=None):
        """Отображает красивую карточку с содержимым."""
        card_html = f"""
        <div class="card">
            <div class="card-title">{icon + ' ' if icon else ''}{title}</div>
            <div class="card-content">{content}</div>
            {f'<div style="color: var(--text-secondary); font-size: 0.85rem; margin-top: 0.75rem; border-top: 1px solid var(--border); padding-top: 0.75rem;">{footer}</div>' if footer else ''}
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
    
    def render_badge(self, text, type="primary"):
        """Отображает цветной бейдж для статусов."""
        return f'<span class="badge badge-{type}">{text}</span>'
    
    def render_metric(self, label, value, description=None, delta=None, delta_color="normal"):
        """Отображает метрику с улучшенным форматированием."""
        delta_html = ""
        if delta is not None:
            arrow = "↑" if delta > 0 else "↓" if delta < 0 else ""
            delta_color_style = "color: green" if delta_color == "good" else "color: red" if delta_color == "bad" else "color: grey"
            delta_html = f'<span style="{delta_color_style}">{arrow} {delta}</span>'
        
        metric_html = f"""
        <div style="background-color: var(--secondary-bg); border-radius: var(--radius); padding: 1rem; border: 1px solid var(--border); box-shadow: var(--shadow);">
            <div style="color: var(--text-secondary); font-size: 0.9rem;">{label}</div>
            <div style="font-size: 1.75rem; font-weight: 600; margin: 0.5rem 0;">{value} {delta_html}</div>
            {f'<div style="color: var(--text-secondary); font-size: 0.85rem;">{description}</div>' if description else ''}
        </div>
        """
        return metric_html
    
    def render(self, skip_status_check=False):
        """Метод для переопределения в дочерних классах."""
        raise NotImplementedError("Метод render должен быть реализован в дочернем классе.") 