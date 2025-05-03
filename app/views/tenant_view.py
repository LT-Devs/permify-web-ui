import streamlit as st
from .base_view import BaseView
from app.controllers import BaseController
import os
from dotenv import load_dotenv

class TenantView(BaseView):
    """Представление для управления арендаторами."""
    
    def __init__(self):
        super().__init__()
        self.controller = BaseController()
        # Загружаем переменные окружения
        load_dotenv()
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс управления арендаторами."""
        self.show_header("Управление арендаторами", 
                         "Настройка арендаторов (tenants) в Permify")
        
        if not skip_status_check and not self.show_status():
            return
        
        # Получаем текущего арендатора
        current_tenant = self.get_tenant_id("tenant_view")
        
        # Информация о арендаторах
        st.info("Арендаторы (tenants) в Permify позволяют разделять данные и права доступа между разными организациями или проектами.")
        
        # Отображаем текущие настройки
        st.subheader("Текущие настройки")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Текущий арендатор (tenant):** `{current_tenant}`")
            
            # Параметры подключения к Permify
            permify_host = os.environ.get("PERMIFY_HOST", "http://localhost:9010")
            permify_grpc_host = os.environ.get("PERMIFY_GRPC_HOST", "http://localhost:9011")
            
            st.markdown(f"**Permify API Host:** `{permify_host}`")
            st.markdown(f"**Permify gRPC Host:** `{permify_grpc_host}`")
        
        with col2:
            # Создаем .env файл, если его нет
            env_file = os.path.join(os.getcwd(), '.env')
            if not os.path.exists(env_file):
                with open(env_file, 'w') as f:
                    f.write(f"PERMIFY_TENANT={current_tenant}\n")
                    f.write(f"PERMIFY_HOST={permify_host}\n")
                    f.write(f"PERMIFY_GRPC_HOST={permify_grpc_host}\n")
            
            # Отображаем содержимое .env файла
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    env_content = f.read()
                
                st.markdown("**Содержимое .env файла:**")
                st.code(env_content, language="bash")
        
        # Форма для изменения арендатора
        st.subheader("Изменить арендатора")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            new_tenant = st.text_input(
                "Новый ID арендатора",
                value=current_tenant,
                key="new_tenant_id",
                help="Идентификатор арендатора в Permify. Применяется сразу после изменения."
            )
        
        with col2:
            st.write("")
            st.write("")
            if st.button("Применить", key="apply_tenant"):
                if new_tenant != current_tenant:
                    # Обновляем переменную сессии
                    st.session_state.tenant_id = new_tenant
                    
                    # Обновляем .env файл
                    if os.path.exists(env_file):
                        with open(env_file, 'r') as f:
                            lines = f.readlines()
                        
                        # Обновляем строку с PERMIFY_TENANT
                        with open(env_file, 'w') as f:
                            for line in lines:
                                if line.startswith("PERMIFY_TENANT="):
                                    f.write(f"PERMIFY_TENANT={new_tenant}\n")
                                else:
                                    f.write(line)
                    
                    st.success(f"Арендатор изменен на {new_tenant}")
                    st.rerun()
        
        # Управление подключением к Permify
        st.subheader("Настройки подключения к Permify")
        
        col1, col2 = st.columns(2)
        
        with col1:
            new_permify_host = st.text_input(
                "API Host URL",
                value=permify_host,
                key="new_permify_host",
                help="URL для подключения к Permify API (обычно порт 9010)"
            )
        
        with col2:
            new_permify_grpc_host = st.text_input(
                "gRPC Host URL",
                value=permify_grpc_host,
                key="new_permify_grpc_host",
                help="URL для подключения к Permify gRPC (обычно порт 9011)"
            )
        
        if st.button("Сохранить настройки подключения", key="save_connection"):
            # Обновляем переменные окружения
            os.environ["PERMIFY_HOST"] = new_permify_host
            os.environ["PERMIFY_GRPC_HOST"] = new_permify_grpc_host
            
            # Обновляем .env файл
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    lines = f.readlines()
                
                # Обновляем строки с PERMIFY_HOST и PERMIFY_GRPC_HOST
                with open(env_file, 'w') as f:
                    for line in lines:
                        if line.startswith("PERMIFY_HOST="):
                            f.write(f"PERMIFY_HOST={new_permify_host}\n")
                        elif line.startswith("PERMIFY_GRPC_HOST="):
                            f.write(f"PERMIFY_GRPC_HOST={new_permify_grpc_host}\n")
                        else:
                            f.write(line)
            
            st.success("Настройки подключения обновлены")
            
            # Проверяем статус после обновления
            status, message = self.controller.check_permify_status()
            if status:
                st.success(f"✅ Успешное подключение к Permify: {message}")
            else:
                st.error(f"❌ Ошибка подключения к Permify: {message}") 