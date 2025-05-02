from .base_controller import BaseController
from app.models import AppModel

class AppController(BaseController):
    """Контроллер для управления приложениями в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.app_model = AppModel()
    
    def get_apps(self, tenant_id=None):
        """Получает список приложений на основе схемы и отношений."""
        return self.app_model.get_apps(tenant_id)
    
    def create_app(self, app_name, app_id, actions, tenant_id=None):
        """Создает новое приложение."""
        return self.app_model.create_app(app_name, app_id, actions, tenant_id)
    
    def update_app_actions(self, app_name, actions, tenant_id=None):
        """Обновляет действия приложения."""
        return self.app_model.update_app_actions(app_name, actions, tenant_id)
    
    def assign_user_to_app(self, app_name, app_id, user_id, role, tenant_id=None):
        """Назначает пользователю роль в приложении."""
        return self.app_model.assign_user_to_app(app_name, app_id, user_id, role, tenant_id)
    
    def remove_user_from_app(self, app_name, app_id, user_id, role, tenant_id=None):
        """Удаляет роль пользователя в приложении."""
        return self.app_model.remove_user_from_app(app_name, app_id, user_id, role, tenant_id)
    
    def assign_group_to_app(self, app_name, app_id, group_id, tenant_id=None):
        """Назначает группу приложению."""
        return self.app_model.assign_group_to_app(app_name, app_id, group_id, tenant_id)
    
    def remove_group_from_app(self, app_name, app_id, group_id, tenant_id=None):
        """Удаляет группу из приложения."""
        return self.app_model.remove_group_from_app(app_name, app_id, group_id, tenant_id)
    
    def check_user_permission(self, app_name, app_id, user_id, action, tenant_id=None):
        """Проверяет разрешение пользователя на действие в приложении."""
        return self.app_model.check_user_permission(app_name, app_id, user_id, action, tenant_id)
