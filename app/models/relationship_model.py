from .base_model import BaseModel
from typing import Dict, Any, List, Optional, Tuple, Union

class RelationshipModel(BaseModel):
    """Модель для работы с отношениями (tuples) Permify."""
    
    def get_relationships(self, tenant_id: str = None, filters: Dict[str, Any] = None) -> Tuple[bool, Any]:
        """Получает список отношений с возможностью фильтрации."""
        tenant_id = tenant_id or self.default_tenant
        
        endpoint = f"/v1/tenants/{tenant_id}/data/relationships/read"
        data = {
            "metadata": {
                "snap_token": ""
            },
            "filter": filters or {},
            "page_size": 100
        }
        
        return self.make_api_request(endpoint, data)
    
    def create_relationship(self, entity_type: str, entity_id: str, relation: str, 
                            subject_type: str, subject_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Создает новое отношение."""
        tenant_id = tenant_id or self.default_tenant
        
        endpoint = f"/v1/tenants/{tenant_id}/data/write"
        data = {
            "metadata": {
                "schema_version": ""
            },
            "tuples": [
                {
                    "entity": {"type": entity_type, "id": entity_id},
                    "relation": relation,
                    "subject": {
                        "type": subject_type, 
                        "id": subject_id,
                        "relation": ""
                    }
                }
            ]
        }
        
        success, result = self.make_api_request(endpoint, data)
        if success:
            return True, "Отношение успешно создано"
        else:
            return False, result
    
    def delete_relationship(self, entity_type: str, entity_id: str, relation: str, 
                           subject_type: str, subject_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет отношение."""
        tenant_id = tenant_id or self.default_tenant
        
        endpoint = f"/v1/tenants/{tenant_id}/data/delete"
        data = {
            "metadata": {
                "snap_token": ""
            },
            "tuple_filter": {
                "entity": {
                    "type": entity_type,
                    "ids": [entity_id]
                },
                "relation": relation,
                "subject": {
                    "type": subject_type,
                    "ids": [subject_id],
                    "relation": ""
                }
            },
            "attribute_filter": {}
        }
        
        success, result = self.make_api_request(endpoint, data)
        if success:
            return True, "Отношение успешно удалено"
        else:
            return False, result
    
    def check_permission(self, entity_type: str, entity_id: str, permission: str, 
                         user_id: str, tenant_id: str = None, schema_version: str = None) -> Tuple[bool, Any]:
        """Проверяет разрешение."""
        tenant_id = tenant_id or self.default_tenant
        
        # Подготавливаем данные для запроса
        data = {
            "metadata": {
                "snap_token": "",
                "schema_version": schema_version or "",
                "depth": 20
            },
            "entity": {"type": entity_type, "id": entity_id},
            "permission": permission,
            "subject": {
                "type": "user", 
                "id": user_id,
                "relation": ""
            }
        }
        
        endpoint = f"/v1/tenants/{tenant_id}/permissions/check"
        return self.make_api_request(endpoint, data)
    
    def assign_user_to_group(self, group_id: str, user_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Добавляет пользователя в группу (создает отношение group-member-user)."""
        return self.create_relationship("group", group_id, "member", "user", user_id, tenant_id)
    
    def assign_user_to_app(self, app_name: str, app_id: str, user_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает пользователю роль в приложении (owner, editor, viewer)."""
        if role not in ["owner", "editor", "viewer"]:
            return False, f"Недопустимая роль: {role}. Доступные роли: owner, editor, viewer"
        
        return self.create_relationship(app_name, app_id, role, "user", user_id, tenant_id)
    
    def assign_group_to_app(self, app_name: str, app_id: str, group_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает группу приложению (создает отношение app-member-group)."""
        return self.create_relationship(app_name, app_id, "member", "group", group_id, tenant_id)
    
    def delete_multiple_relationships(self, relationships: List[Dict[str, str]], tenant_id: str = None) -> Tuple[int, int, List[str]]:
        """Удаляет несколько отношений."""
        tenant_id = tenant_id or self.default_tenant
        results = []
        success_count = 0
        error_count = 0
        
        for rel in relationships:
            entity_type = rel.get("entity_type")
            entity_id = rel.get("entity_id")
            relation = rel.get("relation")
            subject_type = rel.get("subject_type")
            subject_id = rel.get("subject_id")
            
            success, message = self.delete_relationship(
                entity_type, entity_id, relation, subject_type, subject_id, tenant_id
            )
            
            if success:
                success_count += 1
            else:
                error_count += 1
                results.append(f"Ошибка удаления {entity_type}:{entity_id} → {relation} → {subject_type}:{subject_id}: {message}")
        
        return success_count, error_count, results 