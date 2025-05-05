from .base_controller import BaseController
from app.models import GroupModel

class GroupController(BaseController):
    """Контроллер для управления группами в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.group_model = GroupModel()
    
    def get_groups(self, tenant_id=None):
        """Получает список групп на основе связей в системе."""
        groups_dict = self.group_model.get_groups(tenant_id)
        # Преобразуем словарь в список для совместимости с представлением
        return list(groups_dict.values()) if isinstance(groups_dict, dict) else groups_dict
    
    def create_group(self, group_id, name, tenant_id=None):
        """Создает новую группу."""
        return self.group_model.create_group(group_id, name, tenant_id)
    
    def add_user_to_group(self, group_id, user_id, tenant_id=None):
        """Добавляет пользователя в группу."""
        return self.group_model.add_user_to_group(group_id, user_id, tenant_id)
    
    def remove_user_from_group(self, group_id, user_id, tenant_id=None):
        """Удаляет пользователя из группы."""
        return self.group_model.remove_user_from_group(group_id, user_id, tenant_id)
    
    def assign_role_to_group(self, group_id, app_name, app_id, role, tenant_id=None):
        """Назначает роль (право) группе для приложения."""
        return self.group_model.assign_role_to_group(group_id, app_name, app_id, role, tenant_id)
    
    def remove_group_from_app(self, group_id, app_name, app_id, role, tenant_id=None):
        """Удаляет группу из приложения."""
        return self.group_model.remove_group_from_app(group_id, app_name, app_id, role, tenant_id)
    
    def remove_role_from_group(self, group_id, app_type, app_id, role, tenant_id=None):
        """Удаляет роль группы из приложения."""
        return self.group_model.remove_role_from_group(group_id, app_type, app_id, role, tenant_id)
    
    def delete_group(self, group_id, tenant_id=None):
        """Удаляет группу и все её отношения в системе."""
        return self.group_model.delete_group_with_relations(group_id, tenant_id)
    
    def assign_multiple_roles_to_group(self, group_id, app_name, app_id, roles, tenant_id=None):
        """Назначает несколько ролей группе для приложения."""
        return self.group_model.assign_multiple_roles_to_group(group_id, app_name, app_id, roles, tenant_id) 