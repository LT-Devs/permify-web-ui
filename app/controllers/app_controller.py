from .base_controller import BaseController
from app.models import AppModel
from typing import Tuple, Dict, List, Any, Optional, Union

class AppController(BaseController):
    """Контроллер для управления приложениями в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.app_model = AppModel()
    
    def get_apps(self, tenant_id=None):
        """Получает список приложений на основе схемы и отношений."""
        return self.app_model.get_apps(tenant_id)
    
    def create_app(self, app_name, app_id, actions, tenant_id=None, metadata=None):
        """Создает новое приложение."""
        return self.app_model.create_app(app_name, app_id, actions, tenant_id, metadata)
    
    def update_app_actions(self, app_name, actions, tenant_id=None):
        """Обновляет действия приложения."""
        return self.app_model.update_app_actions(app_name, actions, tenant_id)
    
    def assign_user_to_app(self, app_name, app_id, user_id, role, tenant_id=None):
        """Назначает пользователю роль в приложении."""
        return self.app_model.assign_user_to_app(app_name, app_id, user_id, role, tenant_id)
    
    def remove_user_from_app(self, app_name, app_id, user_id, role, tenant_id=None):
        """Удаляет роль пользователя в приложении."""
        return self.app_model.remove_user_from_app(app_name, app_id, user_id, role, tenant_id)
    
    def assign_group_to_app(self, app_name: str, app_id: str, group_id: str, role: str = "viewer", tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает группу приложению с определенной ролью."""
        return self.app_model.assign_group_to_app(app_name, app_id, group_id, role, tenant_id)
    
    def remove_group_from_app(self, app_name: str, app_id: str, group_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет роль группы в приложении."""
        return self.app_model.remove_group_from_app(app_name, app_id, group_id, role, tenant_id)
    
    def check_user_permission(self, app_type: str, app_id: str, user_id: str, action: str, tenant_id: str = None) -> Tuple[bool, Dict[str, Any]]:
        """Проверяет разрешение пользователя для действия с приложением."""
        return self.app_model.check_user_permission(app_type, app_id, user_id, action, tenant_id)
    
    def update_app(self, app_type: str, app_id: str, actions: List[Dict[str, Any]], tenant_id: str = None, metadata=None) -> Tuple[bool, str]:
        """Обновляет существующее приложение и его действия."""
        return self.app_model.update_app(app_type, app_id, actions, tenant_id, metadata)
    
    def delete_app(self, app_type: str, app_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет приложение полностью из системы."""
        return self.app_model.delete_app(app_type, app_id, tenant_id)
    
    def get_all_custom_relations(self) -> List[str]:
        """Возвращает список всех пользовательских типов отношений из всех приложений."""
        return self.app_model.get_all_custom_relations()
    
    def force_rebuild_schema(self, tenant_id: str = None) -> Tuple[bool, str]:
        """Принудительно пересоздает схему на основе текущих данных."""
        return self.app_model.force_rebuild_schema(tenant_id)
