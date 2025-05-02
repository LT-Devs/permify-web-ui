from .base_controller import BaseController
from app.models import UserModel

class UserController(BaseController):
    """Контроллер для управления пользователями в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.user_model = UserModel()
    
    def get_users(self, tenant_id=None):
        """Получает список пользователей на основе связей в системе."""
        return self.user_model.get_users(tenant_id)
    
    def create_user(self, user_id, name, tenant_id=None):
        """Создает нового пользователя."""
        return self.user_model.create_user(user_id, name, tenant_id)
    
    def add_user_to_group(self, user_id, group_id, tenant_id=None):
        """Добавляет пользователя в группу."""
        return self.user_model.add_user_to_group(user_id, group_id, tenant_id)
    
    def remove_user_from_group(self, user_id, group_id, tenant_id=None):
        """Удаляет пользователя из группы."""
        return self.user_model.remove_user_from_group(user_id, group_id, tenant_id)
    
    def assign_app_role(self, user_id, app_type, app_id, role, tenant_id=None):
        """Назначает пользователю роль в приложении."""
        return self.user_model.assign_app_role(user_id, app_type, app_id, role, tenant_id)
    
    def remove_app_role(self, user_id, app_type, app_id, role, tenant_id=None):
        """Удаляет роль пользователя в приложении."""
        return self.user_model.remove_app_role(user_id, app_type, app_id, role, tenant_id) 