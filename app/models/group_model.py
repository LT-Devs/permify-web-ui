from .base_model import BaseModel
from .relationship_model import RelationshipModel
from typing import Dict, Any, List, Optional, Tuple, Union

class GroupModel(BaseModel):
    """Модель для управления группами в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.relationship_model = RelationshipModel()
    
    def get_groups(self, tenant_id: str = None) -> List[Dict[str, Any]]:
        """Получает список групп на основе связей в системе."""
        tenant_id = tenant_id or self.default_tenant
        
        # Получаем все отношения
        success, relationships = self.relationship_model.get_relationships(tenant_id)
        if not success:
            return []
        
        # Извлекаем все уникальные группы
        groups = {}
        
        for tuple_data in relationships.get("tuples", []):
            entity = tuple_data.get("entity", {})
            subject = tuple_data.get("subject", {})
            
            # Если это группа как сущность
            if entity.get("type") == "group":
                group_id = entity.get("id")
                if group_id not in groups:
                    groups[group_id] = {
                        "id": group_id,
                        "name": f"Группа {group_id}",
                        "members": [],
                        "app_memberships": []
                    }
                
                # Если это отношение member с пользователем
                if tuple_data.get("relation") == "member" and subject.get("type") == "user":
                    user_id = subject.get("id")
                    if user_id not in groups[group_id]["members"]:
                        groups[group_id]["members"].append(user_id)
            
            # Если это группа как субъект (для связей с приложениями)
            elif subject.get("type") == "group":
                group_id = subject.get("id")
                if group_id not in groups:
                    groups[group_id] = {
                        "id": group_id,
                        "name": f"Группа {group_id}",
                        "members": [],
                        "app_memberships": []
                    }
                
                # Если группа связана с приложением
                if tuple_data.get("relation") == "member":
                    app_type = entity.get("type")
                    app_id = entity.get("id")
                    
                    groups[group_id]["app_memberships"].append({
                        "app_type": app_type,
                        "app_id": app_id
                    })
        
        return list(groups.values())
    
    def create_group(self, group_id: str, name: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Создает новую группу (через создание схемы, если нет)."""
        # В Permify нет прямого API для создания сущностей как таковых
        # Мы создаем группу через отношения, поэтому просто успех
        return True, f"Группа {group_id} создана"
    
    def add_user_to_group(self, group_id: str, user_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Добавляет пользователя в группу."""
        return self.relationship_model.assign_user_to_group(group_id, user_id, tenant_id)
    
    def remove_user_from_group(self, group_id: str, user_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет пользователя из группы."""
        return self.relationship_model.delete_relationship("group", group_id, "member", "user", user_id, tenant_id)
    
    def assign_group_to_app(self, group_id: str, app_type: str, app_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает группу приложению."""
        return self.relationship_model.assign_group_to_app(app_type, app_id, group_id, tenant_id)
    
    def remove_group_from_app(self, group_id: str, app_type: str, app_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет группу из приложения."""
        return self.relationship_model.delete_relationship(app_type, app_id, "member", "group", group_id, tenant_id) 