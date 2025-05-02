from .base_model import BaseModel
from .relationship_model import RelationshipModel
from .schema_model import SchemaModel
from typing import Dict, Any, List, Optional, Tuple, Union

class AppModel(BaseModel):
    """Модель для управления приложениями в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.relationship_model = RelationshipModel()
        self.schema_model = SchemaModel()
    
    def get_apps(self, tenant_id: str = None) -> List[Dict[str, Any]]:
        """Получает список приложений на основе схемы и отношений."""
        tenant_id = tenant_id or self.default_tenant
        
        # Получаем текущую схему, чтобы найти все сущности, которые могут быть приложениями
        success, schema_result = self.schema_model.get_current_schema(tenant_id)
        if not success or not isinstance(schema_result, dict):
            return []
        
        # Извлекаем информацию о сущностях
        entities_info = self.schema_model.extract_entities_info(schema_result)
        
        # Фильтруем сущности, считая приложениями те, у которых есть
        # отношения owner, editor, viewer или permission/action (пропускаем user и group)
        apps = {}
        for entity_name, entity_info in entities_info.items():
            if entity_name in ["user", "group"]:
                continue
                
            relations = entity_info.get("relations", [])
            permissions = entity_info.get("permissions", [])
            
            # Проверяем, есть ли нужные отношения или разрешения
            has_app_relations = any(rel in relations for rel in ["owner", "editor", "viewer", "member"])
            
            if has_app_relations or permissions:
                apps[entity_name] = {
                    "name": entity_name,
                    "display_name": entity_name.capitalize(),
                    "actions": [{"name": perm, "description": f"Разрешение {perm}"} for perm in permissions],
                    "users": [],
                    "groups": []
                }
        
        # Дополняем информацию из отношений
        success, relationships = self.relationship_model.get_relationships(tenant_id)
        if success:
            for tuple_data in relationships.get("tuples", []):
                entity = tuple_data.get("entity", {})
                subject = tuple_data.get("subject", {})
                relation = tuple_data.get("relation", "")
                
                entity_type = entity.get("type")
                entity_id = entity.get("id")
                
                # Если сущность - приложение
                if entity_type in apps:
                    # Если отношение определяет роль пользователя
                    if relation in ["owner", "editor", "viewer"] and subject.get("type") == "user":
                        user_id = subject.get("id")
                        # Создаем ID для этого экземпляра приложения, если его еще нет
                        app_instance_id = f"{entity_type}:{entity_id}"
                        
                        if app_instance_id not in apps:
                            apps[app_instance_id] = {
                                "id": entity_id,
                                "name": entity_type,
                                "display_name": entity_type.capitalize(),
                                "actions": apps[entity_type]["actions"],
                                "users": [],
                                "groups": []
                            }
                        
                        # Добавляем пользователя с его ролью
                        apps[app_instance_id]["users"].append({
                            "user_id": user_id,
                            "role": relation
                        })
                    
                    # Если отношение определяет группу
                    elif relation == "member" and subject.get("type") == "group":
                        group_id = subject.get("id")
                        # Создаем ID для этого экземпляра приложения, если его еще нет
                        app_instance_id = f"{entity_type}:{entity_id}"
                        
                        if app_instance_id not in apps:
                            apps[app_instance_id] = {
                                "id": entity_id,
                                "name": entity_type,
                                "display_name": entity_type.capitalize(),
                                "actions": apps[entity_type]["actions"],
                                "users": [],
                                "groups": []
                            }
                        
                        # Добавляем группу
                        apps[app_instance_id]["groups"].append(group_id)
        
        # Преобразуем словарь в список для вывода
        apps_list = []
        for app_id, app_info in apps.items():
            if ":" in app_id:  # Это экземпляр приложения
                apps_list.append(app_info)
        
        # Добавляем типы приложений (шаблоны) без созданных экземпляров
        for entity_name, entity_info in apps.items():
            if ":" not in entity_name and not any(app["name"] == entity_name for app in apps_list):
                # Это тип приложения без экземпляров
                apps_list.append({
                    "id": "",
                    "name": entity_name,
                    "display_name": entity_name.capitalize(),
                    "actions": entity_info["actions"],
                    "users": [],
                    "groups": [],
                    "is_template": True
                })
        
        return apps_list
    
    def create_app(self, app_name: str, app_id: str, actions: List[Dict[str, Any]], tenant_id: str = None) -> Tuple[bool, str]:
        """Создает новое приложение (через обновление схемы и создание отношений)."""
        tenant_id = tenant_id or self.default_tenant
        
        # Сначала получаем текущую схему
        success, schema_result = self.schema_model.get_current_schema(tenant_id)
        if not success:
            return False, "Не удалось получить текущую схему"
        
        # Проверяем, есть ли уже такое приложение в схеме
        entities_info = self.schema_model.extract_entities_info(schema_result)
        if app_name in entities_info:
            # Приложение уже есть в схеме, просто создаем связи
            return True, f"Приложение {app_name} уже существует в схеме"
        
        # Создаем новую схему с добавленным приложением
        schema_content = schema_result.get("schema_string", "")
        if not schema_content:
            # Создаем схему с нуля
            schema_content = "entity user {}\n\nentity group {\n  relation member @user\n}\n"
        
        # Добавляем новое приложение
        app_schema = f"\nentity {app_name} {{\n"
        app_schema += "  relation owner @user\n"
        app_schema += "  relation editor @user\n"
        app_schema += "  relation viewer @user\n"
        app_schema += "  relation member @group\n\n"
        
        # Добавляем действия
        for action in actions:
            action_name = action["name"]
            action_rule = "owner"
            
            if action.get("editor_allowed", False):
                action_rule += " or editor"
            if action.get("viewer_allowed", False):
                action_rule += " or viewer"
            if action.get("group_allowed", False):
                action_rule += " or member"
                
            app_schema += f"  action {action_name} = {action_rule}\n"
        
        app_schema += "}\n"
        
        # Объединяем схему
        new_schema = schema_content + app_schema
        
        # Валидируем новую схему
        is_valid, validation_msg = self.schema_model.validate_schema(new_schema)
        if not is_valid:
            return False, f"Ошибка валидации схемы: {validation_msg}"
        
        # Создаем новую схему
        success, result = self.schema_model.create_schema(new_schema, tenant_id)
        if not success:
            return False, f"Ошибка при создании схемы: {result}"
        
        return True, f"Приложение {app_name} успешно создано"
    
    def update_app_actions(self, app_name: str, actions: List[Dict[str, Any]], tenant_id: str = None) -> Tuple[bool, str]:
        """Обновляет действия приложения (через обновление схемы)."""
        tenant_id = tenant_id or self.default_tenant
        
        # Получаем текущую схему
        success, schema_result = self.schema_model.get_current_schema(tenant_id)
        if not success:
            return False, "Не удалось получить текущую схему"
        
        schema_content = schema_result.get("schema_string", "")
        if not schema_content:
            return False, "Не удалось получить содержимое схемы"
        
        # Проверяем, есть ли приложение в схеме
        entities_info = self.schema_model.extract_entities_info(schema_result)
        if app_name not in entities_info:
            return False, f"Приложение {app_name} не найдено в схеме"
        
        # Разбираем схему на строки и находим блок приложения
        lines = schema_content.split('\n')
        app_start = -1
        app_end = -1
        
        for i, line in enumerate(lines):
            if line.strip() == f"entity {app_name} {{":
                app_start = i
            elif app_start != -1 and line.strip() == "}":
                app_end = i
                break
        
        if app_start == -1 or app_end == -1:
            return False, f"Не удалось найти блок приложения {app_name} в схеме"
        
        # Собираем новый блок для приложения
        new_app_block = [f"entity {app_name} {{"]
        
        # Сохраняем отношения из текущего блока
        for i in range(app_start + 1, app_end):
            line = lines[i].strip()
            if line.startswith("relation"):
                new_app_block.append(f"  {line}")
        
        # Добавляем стандартные отношения, если их нет
        relations = ["owner @user", "editor @user", "viewer @user", "member @group"]
        for relation in relations:
            relation_line = f"  relation {relation}"
            if not any(line == relation_line for line in new_app_block):
                new_app_block.append(relation_line)
        
        # Добавляем действия
        for action in actions:
            action_name = action["name"]
            action_rule = "owner"
            
            if action.get("editor_allowed", False):
                action_rule += " or editor"
            if action.get("viewer_allowed", False):
                action_rule += " or viewer"
            if action.get("group_allowed", False):
                action_rule += " or member"
                
            new_app_block.append(f"  action {action_name} = {action_rule}")
        
        new_app_block.append("}")
        
        # Собираем новую схему
        new_schema = '\n'.join(lines[:app_start] + new_app_block + lines[app_end+1:])
        
        # Валидируем новую схему
        is_valid, validation_msg = self.schema_model.validate_schema(new_schema)
        if not is_valid:
            return False, f"Ошибка валидации схемы: {validation_msg}"
        
        # Создаем новую схему
        success, result = self.schema_model.create_schema(new_schema, tenant_id)
        if not success:
            return False, f"Ошибка при создании схемы: {result}"
        
        return True, f"Действия приложения {app_name} успешно обновлены"
    
    def assign_user_to_app(self, app_name: str, app_id: str, user_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает пользователю роль в приложении."""
        return self.relationship_model.assign_user_to_app(app_name, app_id, user_id, role, tenant_id)
    
    def remove_user_from_app(self, app_name: str, app_id: str, user_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет роль пользователя в приложении."""
        return self.relationship_model.delete_relationship(app_name, app_id, role, "user", user_id, tenant_id)
    
    def assign_group_to_app(self, app_name: str, app_id: str, group_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает группу приложению."""
        return self.relationship_model.assign_group_to_app(app_name, app_id, group_id, tenant_id)
    
    def remove_group_from_app(self, app_name: str, app_id: str, group_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет группу из приложения."""
        return self.relationship_model.delete_relationship(app_name, app_id, "member", "group", group_id, tenant_id)
    
    def check_user_permission(self, app_name: str, app_id: str, user_id: str, action: str, tenant_id: str = None) -> Tuple[bool, Any]:
        """Проверяет разрешение пользователя на действие в приложении."""
        return self.relationship_model.check_permission(app_name, app_id, action, user_id, tenant_id) 