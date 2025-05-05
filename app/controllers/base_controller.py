from app.models import BaseModel

class BaseController:
    """Базовый контроллер для всех контроллеров."""
    
    def __init__(self):
        self.base_model = BaseModel()
    
    def check_permify_status(self):
        """Проверяет статус сервера Permify."""
        return self.base_model.check_permify_status()
    
    def make_api_request(self, endpoint, data, method="post"):
        """Выполняет API запрос к Permify через BaseModel."""
        return self.base_model.make_api_request(endpoint, data, method) 