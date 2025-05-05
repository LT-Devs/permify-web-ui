#!/usr/bin/env python3
"""
Точка входа для запуска Permify API Manager
"""

import os
import sys
import subprocess

def print_banner():
    """Выводит баннер приложения"""
    banner = """
    ██████  ███████ ██████  ███    ███ ██ ███████ ██    ██ 
    ██   ██ ██      ██   ██ ████  ████ ██ ██       ██  ██  
    ██████  █████   ██████  ██ ████ ██ ██ █████     ████   
    ██      ██      ██   ██ ██  ██  ██ ██ ██         ██    
    ██      ███████ ██   ██ ██      ██ ██ ██         ██
    
    ███████ ██████  ██     ███    ███  █████  ███    ██  █████   ██████  ███████ ██████
    ██   ██ ██   ██ ██     ████  ████ ██   ██ ████   ██ ██   ██ ██       ██      ██   ██
    ███████ ██████  ██     ██ ████ ██ ███████ ██ ██  ██ ███████ ██   ███ █████   ██████ 
    ██   ██ ██      ██     ██  ██  ██ ██   ██ ██  ██ ██ ██   ██ ██    ██ ██      ██   ██
    ██   ██ ██      ██     ██      ██ ██   ██ ██   ████ ██   ██  ██████  ███████ ██   ██
    """
    print(banner)
    print("Веб-интерфейс для управления Permify")
    print("Версия 2.0.2a\n")

def check_requirements():
    """Проверяет, установлены ли все зависимости"""
    try:
        import streamlit
        import pandas
        import requests
        return True
    except ImportError as e:
        print(f"Ошибка: не установлены все необходимые зависимости: {e}")
        print("Установите их с помощью команды:")
        print("pip install -r requirements.txt")
        return False

def run_streamlit():
    """Запускает приложение Streamlit"""
    try:
        # Добавляем директорию приложения в путь Python
        sys.path.append(os.path.dirname(os.path.abspath(__file__)))
        
        # Запускаем Streamlit
        current_dir = os.path.dirname(os.path.abspath(__file__))
        app_path = os.path.join(current_dir, "permify_app_v2.py")
        
        print("Запуск Permify API Manager...")
        print(f"Используется приложение: {app_path}")
        print("Веб-интерфейс будет доступен по адресу: http://localhost:8501")
        print("\nНажмите Ctrl+C для остановки сервера\n")
        
        # Запускаем Streamlit как subprocess
        subprocess.run([sys.executable, "-m", "streamlit", "run", app_path])
        
    except Exception as e:
        print(f"Ошибка при запуске Streamlit: {e}")
        return False
    
    return True

def main():
    """Основная функция"""
    print_banner()
    
    if not check_requirements():
        return 1
    
    if not run_streamlit():
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 