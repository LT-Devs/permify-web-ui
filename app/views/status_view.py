import streamlit as st
import requests
import socket
import os
from .base_view import BaseView

class StatusView(BaseView):
    """Представление для отображения статуса системы."""
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс статуса системы."""
        self.show_header("Статус системы", "Информация о состоянии Permify и его компонентов")
        
        # Информация о Permify
        st.subheader("Информация о Permify")
        
        # Проверяем статус
        status, message = self.controller.check_permify_status()
        if status:
            st.success(f"✅ Permify доступен: {message}")
        else:
            st.error(f"❌ Permify недоступен: {message}")
        
        # Информация о подключении
        permify_host = os.environ.get("PERMIFY_HOST", "http://localhost:9010")
        permify_grpc_host = os.environ.get("PERMIFY_GRPC_HOST", "http://localhost:9011")
        default_tenant = os.environ.get("PERMIFY_TENANT", "t1")
        
        st.write(f"**REST API URL:** {permify_host}")
        st.write(f"**gRPC API URL:** {permify_grpc_host}")
        st.write(f"**Арендатор по умолчанию:** {default_tenant}")
        
        # Проверка статуса портов
        st.subheader("Проверка API портов")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Проверить REST API"):
                try:
                    response = requests.get(f"{permify_host}/healthz")
                    st.code(f"Статус: {response.status_code}\nОтвет: {response.text}")
                except Exception as e:
                    st.error(f"Ошибка соединения: {str(e)}")
        
        with col2:
            if st.button("Проверить gRPC API"):
                try:
                    host, port = permify_grpc_host.replace("http://", "").replace("https://", "").split(":")
                    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    result = sock.connect_ex((host, int(port)))
                    if result == 0:
                        st.success(f"✅ Порт {port} открыт")
                    else:
                        st.error(f"❌ Порт {port} закрыт")
                    sock.close()
                except Exception as e:
                    st.error(f"Ошибка проверки порта: {str(e)}")
        
        # Системная информация
        st.subheader("Информация о системе")
        st.write(f"**Операционная система:** {os.name}")
        
        # Проверка зависимостей
        st.subheader("Зависимости Python")
        try:
            import pkg_resources
            installed_packages = {pkg.key: pkg.version for pkg in pkg_resources.working_set}
            
            dependencies = {
                "streamlit": "Streamlit",
                "pandas": "Pandas",
                "requests": "Requests"
            }
            
            for package, display_name in dependencies.items():
                if package in installed_packages:
                    st.write(f"✅ {display_name}: {installed_packages[package]}")
                else:
                    st.write(f"❌ {display_name}: не установлен")
        except Exception as e:
            st.error(f"Ошибка при проверке зависимостей: {str(e)}")
        
        # Информация о приложении
        st.subheader("О приложении")
        st.markdown("""
        ### О приложении
        **Permify API Manager** - это приложение для управления схемами и отношениями в системе авторизации Permify.
        
        **Режимы работы:**
        - **Упрощенный режим** - для администраторов, работающих с пользователями, группами и приложениями
        - **Ручной режим** - для разработчиков, работающих напрямую со схемами и отношениями
        
        **Версия:** 2.0.0
        """)
        
        # Ссылки на документацию
        st.markdown("""
        ### Полезные ссылки
        - [Документация Permify](https://docs.permify.co/)
        - [GitHub Permify](https://github.com/Permify/permify)
        - [Форум Permify](https://github.com/Permify/permify/discussions)
        """)
        
        # Отладочная информация
        with st.expander("Отладочная информация"):
            st.code(f"""
            PERMIFY_HOST: {permify_host}
            PERMIFY_GRPC_HOST: {permify_grpc_host}
            DEFAULT_TENANT: {default_tenant}
            Python version: {os.sys.version}
            """)
            
            st.subheader("Переменные окружения")
            for key, value in dict(os.environ).items():
                if "PERMIFY" in key or "PATH" in key:
                    st.write(f"**{key}:** {value}")
                
            st.subheader("Streamlit config")
            st.write("Информация о конфигурации Streamlit") 