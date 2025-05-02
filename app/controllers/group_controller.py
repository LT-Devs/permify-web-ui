from .base_controller import BaseController
from app.models import GroupModel

class GroupController(BaseController):
    """Контроллер для управления группами в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.group_model = GroupModel()
    
    def get_groups(self, tenant_id=None):
        """Получает список групп на основе связей в системе."""
        return self.group_model.get_groups(tenant_id)
    
    def create_group(self, group_id, name, tenant_id=None):
        """Создает новую группу."""
        return self.group_model.create_group(group_id, name, tenant_id)
    
    def add_user_to_group(self, group_id, user_id, tenant_id=None):
        """Добавляет пользователя в группу."""
        return self.group_model.add_user_to_group(group_id, user_id, tenant_id)
    
    def remove_user_from_group(self, group_id, user_id, tenant_id=None):
        """Удаляет пользователя из группы."""
        return self.group_model.remove_user_from_group(group_id, user_id, tenant_id)
    
    def assign_group_to_app(self, group_id, app_type, app_id, tenant_id=None):
        """Назначает группу приложению."""
        return self.group_model.assign_group_to_app(group_id, app_type, app_id, tenant_id)
    
    def remove_group_from_app(self, group_id, app_type, app_id, tenant_id=None):
        """Удаляет группу из приложения."""
        return self.group_model.remove_group_from_app(group_id, app_type, app_id, tenant_id) 