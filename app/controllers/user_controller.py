from .base_controller import BaseController
from app.models import UserModel
from .redis_controller import RedisController

class UserController(BaseController):
    """Контроллер для управления пользователями в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.user_model = UserModel()
        self.redis_controller = RedisController()
    
    def get_users(self, tenant_id=None):
        """Получает список пользователей на основе связей в системе."""
        return self.user_model.get_users(tenant_id)
    
    def create_user(self, user_id, name, tenant_id=None):
        """Создает нового пользователя."""
        return self.user_model.create_user(user_id, name, tenant_id)
    
    def add_user_to_group(self, user_id, group_id, tenant_id=None):
        """Добавляет пользователя в группу."""
        success, message = self.user_model.add_user_to_group(user_id, group_id, tenant_id)
        if success:
            # Сбрасываем кэш для пользователя при изменении его групп
            self.redis_controller.flush_user_permissions(user_id)
        return success, message
    
    def remove_user_from_group(self, user_id, group_id, tenant_id=None):
        """Удаляет пользователя из группы."""
        success, message = self.user_model.remove_user_from_group(user_id, group_id, tenant_id)
        if success:
            # Сбрасываем кэш для пользователя при изменении его групп
            self.redis_controller.flush_user_permissions(user_id)
        return success, message
    
    def assign_app_role(self, user_id, app_type, app_id, role, tenant_id=None):
        """Назначает пользователю роль в приложении."""
        success, message = self.user_model.assign_app_role(user_id, app_type, app_id, role, tenant_id)
        if success:
            # Сбрасываем кэш для пользователя при изменении его ролей
            self.redis_controller.flush_user_permissions(user_id)
            # Также сбрасываем кэш для приложения/сущности
            self.redis_controller.flush_entity_permissions(app_type, app_id)
        return success, message
    
    def remove_app_role(self, user_id, app_type, app_id, role, tenant_id=None):
        """Удаляет роль пользователя в приложении."""
        success, message = self.user_model.remove_app_role(user_id, app_type, app_id, role, tenant_id)
        if success:
            # Сбрасываем кэш для пользователя при изменении его ролей
            self.redis_controller.flush_user_permissions(user_id)
            # Также сбрасываем кэш для приложения/сущности
            self.redis_controller.flush_entity_permissions(app_type, app_id)
        return success, message
    
    def delete_user(self, user_id, tenant_id=None):
        """Удаляет пользователя и все его отношения в системе."""
        # Сбрасываем кэш для пользователя перед удалением
        self.redis_controller.flush_user_permissions(user_id)
        return self.user_model.delete_user_with_relations(user_id, tenant_id) 