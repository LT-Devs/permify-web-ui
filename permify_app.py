import streamlit as st
import requests
import json
import time
import os
import tempfile
import subprocess
import io
from pathlib import Path
import pandas as pd
from app.views.styles import get_modern_styles

# Настройки Permify API из переменных окружения
PERMIFY_HOST = os.environ.get("PERMIFY_HOST", "http://localhost:9010")
PERMIFY_GRPC_HOST = os.environ.get("PERMIFY_GRPC_HOST", "http://localhost:9011")
DEFAULT_TENANT = os.environ.get("PERMIFY_TENANT", "t1")

# Настройка страницы Streamlit
st.set_page_config(
    page_title="Permify - Система управления доступом",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Применяем современные стили
st.markdown(get_modern_styles(), unsafe_allow_html=True)

# Заголовок приложения
st.title("🔐 Permify API Manager")
st.sidebar.header("Управление")

# Для отладки показываем используемые хосты
st.sidebar.write(f"API Host: {PERMIFY_HOST}")
st.sidebar.write(f"gRPC Host: {PERMIFY_GRPC_HOST}")

# Добавляем оформление сайдбара
st.sidebar.markdown('<div class="divider"></div>', unsafe_allow_html=True)

# Функция для выбора файлов на сервере
def server_file_selector(folder_path='.', extensions=None):
    try:
        files = []
        for item in Path(folder_path).glob('**/*'):
            if item.is_file():
                if extensions is None or item.suffix.lower().lstrip('.') in extensions:
                    files.append(str(item))
        
        if not files:
            st.warning(f"В директории {folder_path} не найдено файлов" + 
                       (f" с расширениями: {', '.join(extensions)}" if extensions else ""))
            return None
            
        selected_file = st.selectbox('Выберите файл', sorted(files))
        return selected_file
    except Exception as e:
        st.error(f"Ошибка при сканировании файлов: {str(e)}")
        return None

# Функция для проверки статуса Permify
def check_permify_status():
    try:
        response = requests.get(f"{PERMIFY_HOST}/healthz")
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "SERVING":
                return True, "Сервер работает"
        return False, f"Ошибка статуса: {response.text}"
    except Exception as e:
        return False, f"Ошибка соединения: {str(e)}"

# Проверка статуса сервера
status, message = check_permify_status()
if status:
    # Используем современное оформление для уведомлений
    st.markdown("""
    <div style="background-color: rgba(40, 167, 69, 0.1); border: 1px solid rgba(40, 167, 69, 0.5); color: var(--text); padding: 1rem; border-radius: var(--radius); margin: 1rem 0;">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 1.5rem; margin-right: 0.75rem;">✅</span>
            <div>
                <div style="font-weight: 600; font-size: 1.1rem;">Сервер Permify работает</div>
                <div style="margin-top: 0.25rem; font-size: 0.9rem;">Все системы функционируют нормально.</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Сообщение об ошибке с улучшенным форматированием
    st.markdown(f"""
    <div style="background-color: rgba(220, 53, 69, 0.1); border: 1px solid rgba(220, 53, 69, 0.5); color: var(--text); padding: 1rem; border-radius: var(--radius); margin: 1rem 0;">
        <div style="display: flex; align-items: center;">
            <span style="font-size: 1.5rem; margin-right: 0.75rem;">❌</span>
            <div>
                <div style="font-weight: 600; font-size: 1.1rem;">Сервер Permify недоступен</div>
                <div style="margin-top: 0.25rem; font-size: 0.9rem;">{message}</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Используем приложение из модульной структуры
from app.main import main

# Запускаем приложение
main()

# Добавляем информацию о системе внизу страницы
st.markdown('<div class="divider"></div>', unsafe_allow_html=True)
st.caption("Permify API Manager | Версия 2.0.1a | © 2023 BadKiko (LT-Devs)") 