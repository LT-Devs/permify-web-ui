from .base_model import BaseModel
from .relationship_model import RelationshipModel
from typing import Dict, Any, List, Optional, Tuple, Union

class UserModel(BaseModel):
    """Модель для управления пользователями в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.relationship_model = RelationshipModel()
    
    def get_users(self, tenant_id: str = None) -> List[Dict[str, Any]]:
        """Получает список пользователей на основе связей в системе."""
        tenant_id = tenant_id or self.default_tenant
        
        # Получаем все отношения
        success, relationships = self.relationship_model.get_relationships(tenant_id)
        if not success:
            return []
        
        # Извлекаем всех уникальных пользователей
        users = {}
        
        for tuple_data in relationships.get("tuples", []):
            subject = tuple_data.get("subject", {})
            entity = tuple_data.get("entity", {})
            
            # Добавляем пользователей из субъектов
            if subject.get("type") == "user":
                user_id = subject.get("id")
                if user_id not in users:
                    users[user_id] = {
                        "id": user_id,
                        "name": f"Пользователь {user_id}",
                        "groups": [],
                        "app_roles": []
                    }
                
                # Если это связь с группой, добавляем группу пользователю
                if entity.get("type") == "group" and tuple_data.get("relation") == "member":
                    group_id = entity.get("id")
                    if group_id not in users[user_id]["groups"]:
                        users[user_id]["groups"].append(group_id)
                
                # Если это связь с приложением, добавляем роль пользователю
                elif tuple_data.get("relation") in ["owner", "editor", "viewer"]:
                    app_type = entity.get("type")
                    app_id = entity.get("id")
                    role = tuple_data.get("relation")
                    
                    users[user_id]["app_roles"].append({
                        "app_type": app_type,
                        "app_id": app_id,
                        "role": role
                    })
        
        return list(users.values())
    
    def create_user(self, user_id: str, name: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Создает нового пользователя (метод-заглушка, т.к. в Permify нет прямого управления пользователями)."""
        # В Permify нет явных пользователей, они создаются через отношения
        # Поэтому этот метод на самом деле ничего не делает в API
        # Но в реальном приложении здесь может быть интеграция с системой управления пользователями
        
        return True, f"Пользователь {user_id} добавлен в систему"
    
    def add_user_to_group(self, user_id: str, group_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Добавляет пользователя в группу."""
        return self.relationship_model.assign_user_to_group(group_id, user_id, tenant_id)
    
    def remove_user_from_group(self, user_id: str, group_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет пользователя из группы."""
        return self.relationship_model.delete_relationship("group", group_id, "member", "user", user_id, tenant_id)
    
    def assign_app_role(self, user_id: str, app_type: str, app_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает пользователю роль в приложении."""
        return self.relationship_model.assign_user_to_app(app_type, app_id, user_id, role, tenant_id)
    
    def remove_app_role(self, user_id: str, app_type: str, app_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет роль пользователя в приложении."""
        return self.relationship_model.delete_relationship(app_type, app_id, role, "user", user_id, tenant_id) 