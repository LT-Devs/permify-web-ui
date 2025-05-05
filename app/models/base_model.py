import requests
import os
from typing import Dict, Any, List, Optional, Tuple, Union
import json

class BaseModel:
    """Базовый класс для всех моделей с общей функциональностью API."""
    
    def __init__(self):
        # Настройки Permify API из переменных окружения
        self.permify_host = os.environ.get("PERMIFY_HOST", "http://localhost:9010")
        self.permify_grpc_host = os.environ.get("PERMIFY_GRPC_HOST", "http://localhost:9011")
        self.default_tenant = os.environ.get("PERMIFY_TENANT", "t1")
    
    def check_permify_status(self) -> Tuple[bool, str]:
        """Проверяет статус сервера Permify"""
        try:
            response = requests.get(f"{self.permify_host}/healthz")
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "SERVING":
                    return True, "Сервер работает"
            return False, f"Ошибка статуса: {response.text}"
        except Exception as e:
            return False, f"Ошибка соединения: {str(e)}"
    
    def make_api_request(self, endpoint: str, data: Dict[str, Any], method: str = "post") -> Tuple[bool, Any]:
        """Выполняет API запрос к Permify"""
        try:
            url = f"{self.permify_host}{endpoint}"
            print(f"DEBUG: API запрос: URL={url}, Метод={method}")
            
            if method.lower() == "post":
                print(f"DEBUG: POST данные: {json.dumps(data, indent=2)}")
                response = requests.post(
                    url,
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
            elif method.lower() == "get":
                print(f"DEBUG: GET параметры: {data}")
                response = requests.get(
                    url,
                    params=data,
                    headers={"Content-Type": "application/json"}
                )
            else:
                return False, f"Неподдерживаемый метод: {method}"
            
            print(f"DEBUG: Статус ответа: {response.status_code}")
            print(f"DEBUG: Заголовки ответа: {dict(response.headers)}")
            
            try:
                response_text = response.text
                print(f"DEBUG: Текст ответа: {response_text}")
                response_json = response.json() if response_text else {}
            except Exception as e:
                print(f"DEBUG: Ошибка при парсинге JSON: {str(e)}")
                response_json = {}
            
            if response.status_code == 200:
                return True, response_json
            else:
                return False, f"Ошибка API: {response.status_code} - {response_text}"
        except Exception as e:
            import traceback
            traceback_text = traceback.format_exc()
            print(f"DEBUG: Исключение в make_api_request: {str(e)}")
            print(f"DEBUG: Трассировка:\n{traceback_text}")
            return False, f"Ошибка запроса: {str(e)}\n{traceback_text}" 