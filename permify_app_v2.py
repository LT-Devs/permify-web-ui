import os
import sys

# Добавляем директорию приложения в путь Python
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import main

if __name__ == "__main__":
    main() 