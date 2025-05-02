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
            
            if method.lower() == "post":
                response = requests.post(
                    url,
                    json=data,
                    headers={"Content-Type": "application/json"}
                )
            elif method.lower() == "get":
                response = requests.get(
                    url,
                    params=data,
                    headers={"Content-Type": "application/json"}
                )
            else:
                return False, f"Неподдерживаемый метод: {method}"
            
            if response.status_code == 200:
                return True, response.json()
            else:
                return False, f"Ошибка API: {response.status_code} - {response.text}"
        except Exception as e:
            import traceback
            return False, f"Ошибка запроса: {str(e)}\n{traceback.format_exc()}" 