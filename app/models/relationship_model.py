from .base_model import BaseModel
from typing import Dict, Any, List, Optional, Tuple, Union
import os
import json

class RelationshipModel(BaseModel):
    """Модель для работы с отношениями (tuples) Permify."""
    
    def __init__(self):
        super().__init__()
        self.relationships_file = os.path.join(os.getcwd(), 'data', 'relationships.json')
        
        # Создаем директорию data, если она не существует
        os.makedirs(os.path.dirname(self.relationships_file), exist_ok=True)
        
        # Создаем файл с пустым списком отношений, если он не существует
        if not os.path.exists(self.relationships_file):
            with open(self.relationships_file, 'w') as f:
                json.dump({"tuples": []}, f, indent=2)
    
    def _load_relationships(self) -> Dict[str, List[Dict[str, Any]]]:
        """Загружает отношения из файла."""
        try:
            with open(self.relationships_file, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {"tuples": []}
    
    def _save_relationships(self, relationships: Dict[str, List[Dict[str, Any]]]) -> bool:
        """Сохраняет отношения в файл."""
        try:
            with open(self.relationships_file, 'w') as f:
                json.dump(relationships, f, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении отношений: {str(e)}")
            return False
    
    def get_relationships(self, tenant_id: str = None, filters: Dict[str, Any] = None) -> Tuple[bool, Any]:
        """Получает список отношений с возможностью фильтрации."""
        tenant_id = tenant_id or self.default_tenant
        
        # Загружаем отношения из файла
        relationships = self._load_relationships()
        
        # Применяем фильтрацию, если нужно
        if filters:
            filtered_tuples = []
            for tuple_data in relationships.get("tuples", []):
                matches = True
                
                # Фильтр по типу сущности
                if "entity_type" in filters and tuple_data.get("entity", {}).get("type") != filters["entity_type"]:
                    matches = False
                
                # Фильтр по ID сущности
                if "entity_id" in filters and tuple_data.get("entity", {}).get("id") != filters["entity_id"]:
                    matches = False
                
                # Фильтр по отношению
                if "relation" in filters and tuple_data.get("relation") != filters["relation"]:
                    matches = False
                
                # Фильтр по типу субъекта
                if "subject_type" in filters and tuple_data.get("subject", {}).get("type") != filters["subject_type"]:
                    matches = False
                
                # Фильтр по ID субъекта
                if "subject_id" in filters and tuple_data.get("subject", {}).get("id") != filters["subject_id"]:
                    matches = False
                
                if matches:
                    filtered_tuples.append(tuple_data)
            
            return True, {"tuples": filtered_tuples}
        
        # В режиме локальной разработки просто возвращаем все отношения
        return True, relationships
    
    def create_relationship(self, entity_type: str, entity_id: str, relation: str, 
                            subject_type: str, subject_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Создает новое отношение."""
        tenant_id = tenant_id or self.default_tenant
        
        # Загружаем текущие отношения
        relationships = self._load_relationships()
        
        # Проверяем, существует ли уже такое отношение
        for tuple_data in relationships.get("tuples", []):
            entity = tuple_data.get("entity", {})
            subject = tuple_data.get("subject", {})
            
            if (entity.get("type") == entity_type and 
                entity.get("id") == entity_id and 
                tuple_data.get("relation") == relation and 
                subject.get("type") == subject_type and 
                subject.get("id") == subject_id):
                return True, "Отношение уже существует"
        
        # Создаем новое отношение
        new_tuple = {
            "entity": {"type": entity_type, "id": entity_id},
            "relation": relation,
            "subject": {
                "type": subject_type, 
                "id": subject_id,
                "relation": ""
            }
        }
        
        # Добавляем к текущим отношениям
        relationships["tuples"].append(new_tuple)
        
        # Сохраняем обновленные отношения
        if self._save_relationships(relationships):
            # Пытаемся также сохранить через API, если доступно
            try:
                # Подготавливаем данные для API запроса
                endpoint = f"/v1/tenants/{tenant_id}/data/write"
                data = {
                    "metadata": {
                        "schema_version": ""
                    },
                    "tuples": [new_tuple]
                }
                
                # Делаем API запрос, но игнорируем результат - локальное хранилище важнее
                self.make_api_request(endpoint, data)
            except Exception:
                pass  # Игнорируем ошибки API, так как у нас уже есть локальное хранилище
            
            return True, "Отношение успешно создано"
        else:
            return False, "Ошибка при сохранении отношения"
    
    def delete_relationship(self, entity_type: str, entity_id: str, relation: str, 
                           subject_type: str, subject_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет отношение."""
        tenant_id = tenant_id or self.default_tenant
        
        # Загружаем текущие отношения
        relationships = self._load_relationships()
        
        # Ищем и удаляем отношение
        updated_tuples = []
        found = False
        
        for tuple_data in relationships.get("tuples", []):
            entity = tuple_data.get("entity", {})
            subject = tuple_data.get("subject", {})
            
            if (entity.get("type") == entity_type and 
                entity.get("id") == entity_id and 
                tuple_data.get("relation") == relation and 
                subject.get("type") == subject_type and 
                subject.get("id") == subject_id):
                found = True
                continue  # Пропускаем это отношение (удаляем)
            
            updated_tuples.append(tuple_data)
        
        if not found:
            return False, "Отношение не найдено"
        
        # Обновляем отношения
        relationships["tuples"] = updated_tuples
        
        # Сохраняем обновленные отношения
        if self._save_relationships(relationships):
            # Пытаемся также удалить через API, если доступно
            try:
                # Подготавливаем данные для API запроса
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
                
                # Делаем API запрос, но игнорируем результат - локальное хранилище важнее
                self.make_api_request(endpoint, data)
            except Exception:
                pass  # Игнорируем ошибки API, так как у нас уже есть локальное хранилище
            
            return True, "Отношение успешно удалено"
        else:
            return False, "Ошибка при удалении отношения"
    
    def check_permission(self, entity_type: str, entity_id: str, permission: str, 
                         user_id: str, tenant_id: str = None, schema_version: str = None) -> Tuple[bool, Any]:
        """Проверяет разрешение."""
        tenant_id = tenant_id or self.default_tenant
        
        # Для локальной проверки доступа сначала пытаемся использовать API
        try:
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
            success, result = self.make_api_request(endpoint, data)
            
            if success:
                return True, result
        except Exception:
            pass  # При ошибке API продолжаем с локальной проверкой
        
        # В режиме локальной разработки просто возвращаем положительный результат
        # В реальном приложении здесь должен быть логика проверки доступа на основе ролей и прав
        return True, {
            "can": True,
            "metadata": {
                "reason": "Local development mode - access granted by default"
            }
        }
    
    def assign_user_to_group(self, group_id: str, user_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Добавляет пользователя в группу (создает отношение group-member-user)."""
        return self.create_relationship("group", group_id, "member", "user", user_id, tenant_id)
    
    def assign_user_to_app(self, app_name: str, app_id: str, user_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает пользователю роль в приложении (owner, editor, viewer и пользовательские роли)."""
        # Стандартные роли
        standard_roles = ["owner", "editor", "viewer"]
        
        # Если не стандартная роль, проверяем есть ли она в метаданных приложения
        if role not in standard_roles:
            # Загружаем приложения
            # Импортируем здесь, чтобы избежать циклической зависимости
            from app.models.app_model import AppModel
            app_model = AppModel()
            
            # Получаем список приложений
            apps = app_model.get_apps(tenant_id)
            
            # Ищем указанное приложение
            app = next((a for a in apps if a.get('name') == app_name and a.get('id') == app_id), None)
            
            # Проверяем наличие пользовательской роли в метаданных
            custom_roles = []
            if app and 'metadata' in app and 'custom_relations' in app.get('metadata', {}):
                custom_roles = app.get('metadata', {}).get('custom_relations', [])
            
            # Если роль не найдена в пользовательских ролях, возвращаем ошибку
            if role not in custom_roles:
                available_roles = standard_roles + custom_roles
                return False, f"Недопустимая роль: {role}. Доступные роли: {', '.join(available_roles)}"
        
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