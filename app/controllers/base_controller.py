from app.models import BaseModel

class BaseController:
    """Базовый контроллер для всех контроллеров."""
    
    def __init__(self):
        self.base_model = BaseModel()
    
    def check_permify_status(self):
        """Проверяет статус сервера Permify."""
        return self.base_model.check_permify_status() 