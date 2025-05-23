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
        """Проверяет разрешение пользователя на действие для сущности."""
        tenant_id = tenant_id or self.default_tenant
        
        # Первый запрос - прямая проверка для пользователя
        endpoint = f"/v1/tenants/{tenant_id}/permissions/check"
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
                "id": user_id
            }
        }
        
        try:
            success, result = self.make_api_request(endpoint, data)
            
            if success:
                # Если у нас нет метаданных по какой-то причине, добавим пустые
                if 'metadata' not in result:
                    result['metadata'] = {}
                
                # В новой схеме права групп автоматически проверяются через цепочку отношений
                # Например, group_owner.member будет проверен автоматически
                # Но для совместимости со старым кодом и на случай ошибок, добавим дополнительную проверку:
                
                # Если доступ запрещен, попробуем проверить группы вручную
                if not result.get("can") and result.get("can") != "CHECK_RESULT_ALLOWED":
                    # Получаем группы пользователя
                    user_groups = self.get_user_groups(user_id, tenant_id)
                    
                    # Для каждой группы проверяем права напрямую
                    for group_id in user_groups:
                        # Проверяем права с явным указанием group_* ролей
                        for role_prefix in ["group_owner", "group_editor", "group_viewer"]:
                            # Проверяем наличие такого отношения
                            has_relation = self.check_relationship_exists(
                                entity_type, entity_id, role_prefix, "group", group_id, tenant_id
                            )
                            
                            if has_relation:
                                # Если отношение существует, проверяем разрешение напрямую
                                if self._check_role_grants_permission(role_prefix, permission):
                                    result["can"] = True
                                    result["metadata"]["reason"] = f"Доступ предоставлен через роль {role_prefix} группы (группа: {group_id})"
                                    break
                
                return success, result
            else:
                return False, result
        except Exception as e:
            return False, f"Ошибка при проверке разрешения: {str(e)}"
    
    def _check_role_grants_permission(self, role: str, permission: str) -> bool:
        """Проверяет, дает ли роль доступ к запрашиваемому разрешению."""
        # Карта ролей и их прав
        role_permissions = {
            "owner": ["view", "edit", "delete", "create", "export", "read", "write", "manage"],
            "editor": ["view", "edit", "read", "write"],
            "viewer": ["view", "read"],
            "group_owner": ["view", "edit", "delete", "create", "export", "read", "write", "manage"],
            "group_editor": ["view", "edit", "read", "write"],
            "group_viewer": ["view", "read"]
        }
        
        # Для кастомных ролей группы с префиксом group_* предоставляем соответствующие права
        if role.startswith("group_") and role not in role_permissions:
            # Извлекаем базовую роль без префикса group_
            base_role = role[6:]  # убираем 'group_'
            
            # Предполагаем, что кастомная роль дает те же права, что и стандартная с таким же названием
            # Или, если такой стандартной роли нет, предоставляем базовый набор прав (view, read)
            if base_role in role_permissions:
                return permission in role_permissions[base_role]
            else:
                # Для неизвестных кастомных ролей предоставляем доступ к permission, если оно совпадает с именем роли
                # Например, роль group_view_petitions дает доступ к permission view_petitions
                if permission == base_role:
                    return True
                return permission in ["view", "read"]  # базовый набор прав для всех кастомных ролей
        
        # Если роль неизвестна или разрешение не указано, запрещаем
        if role not in role_permissions or not permission:
            return False
        
        # Проверяем наличие разрешения в списке разрешенных для роли
        return permission in role_permissions[role]
    
    def check_relationship_exists(self, entity_type: str, entity_id: str, relation: str, 
                                 subject_type: str, subject_id: str, tenant_id: str = None) -> bool:
        """Проверяет существование указанного отношения."""
        tenant_id = tenant_id or self.default_tenant
        
        # Получаем все отношения
        success, relationships = self.get_relationships(tenant_id)
        if not success:
            return False
        
        # Ищем нужное отношение
        for tuple_data in relationships.get("tuples", []):
            entity = tuple_data.get("entity", {})
            subject = tuple_data.get("subject", {})
            rel = tuple_data.get("relation", "")
            
            if (entity.get("type") == entity_type and 
                entity.get("id") == entity_id and
                rel == relation and
                subject.get("type") == subject_type and
                subject.get("id") == subject_id):
                
                return True
        
        return False
    
    def get_user_groups(self, user_id: str, tenant_id: str = None) -> List[str]:
        """Получает список групп, в которых состоит пользователь."""
        tenant_id = tenant_id or self.default_tenant
        
        # Получаем все отношения
        success, relationships = self.get_relationships(tenant_id)
        if not success:
            return []
        
        # Ищем группы пользователя
        user_groups = []
        for tuple_data in relationships.get("tuples", []):
            entity = tuple_data.get("entity", {})
            subject = tuple_data.get("subject", {})
            relation = tuple_data.get("relation", "")
            
            # Проверяем, что это отношение member между группой и пользователем
            if (entity.get("type") == "group" and 
                relation == "member" and
                subject.get("type") == "user" and
                subject.get("id") == user_id):
                
                user_groups.append(entity.get("id"))
        
        return user_groups
    
    def assign_user_to_group(self, group_id: str, user_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Добавляет пользователя в группу (создает отношение group-member-user)."""
        return self.create_relationship("group", group_id, "member", "user", user_id, tenant_id)
    
    def assign_role_to_group(self, group_id: str, entity_type: str, entity_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает роль группе для сущности."""
        tenant_id = tenant_id or self.default_tenant
        
        # Получаем текущую версию схемы
        from .schema_model import SchemaModel
        schema_model = SchemaModel()
        schema_version = ""
        
        try:
            success, schema_result = schema_model.get_current_schema(tenant_id)
            if success and schema_result and "version" in schema_result:
                schema_version = schema_result["version"]
                print(f"DEBUG: Получена версия схемы: {schema_version}")
            else:
                print(f"DEBUG: Не удалось получить версию схемы, success={success}, result={schema_result}")
        except Exception as e:
            print(f"Ошибка при получении версии схемы: {str(e)}")
        
        # Добавляем префикс group_ к роли для отличия от пользовательских ролей
        # Преобразуем стандартные роли в формат с префиксом group_
        group_role_mapping = {
            "owner": "group_owner",
            "editor": "group_editor",
            "viewer": "group_viewer",
            "member": "group_member"
        }
        
        # Используем префикс group_ если это стандартная роль, иначе добавляем префикс group_ к кастомной роли
        if role in group_role_mapping:
            relation = group_role_mapping[role]
        else:
            # Если кастомная роль, добавляем префикс group_
            relation = f"group_{role}"
            
        print(f"DEBUG: Назначение роли группе: {group_id}, роль: {role} -> {relation}, для {entity_type}:{entity_id}")
        
        # Используем правильный формат запроса с массивом tuples
        data = {
            "metadata": {
                "schema_version": schema_version
            },
            "tuples": [
                {
                    "entity": {"type": entity_type, "id": entity_id},
                    "relation": relation,
                    "subject": {"type": "group", "id": group_id}
                }
            ]
        }
        
        # Используем endpoint для записи данных
        endpoint = f"/v1/tenants/{tenant_id}/data/write"
        print(f"DEBUG: Отправка запроса на endpoint: {endpoint}")
        print(f"DEBUG: Содержимое запроса: {data}")
        
        success, result = self.make_api_request(endpoint, data)
        print(f"DEBUG: Результат запроса: success={success}, result={result}")
        
        if success:
            # Добавляем отношение также и в локальное хранилище
            # Загружаем текущие отношения
            relationships = self._load_relationships()
            
            # Создаем новое отношение в том же формате, что и API
            new_tuple = {
                "entity": {"type": entity_type, "id": entity_id},
                "relation": relation,
                "subject": {
                    "type": "group", 
                    "id": group_id,
                    "relation": ""
                }
            }
            
            # Проверяем, существует ли уже такое отношение в локальном хранилище
            exists = False
            for tuple_data in relationships.get("tuples", []):
                entity = tuple_data.get("entity", {})
                subject = tuple_data.get("subject", {})
                
                if (entity.get("type") == entity_type and 
                    entity.get("id") == entity_id and 
                    tuple_data.get("relation") == relation and 
                    subject.get("type") == "group" and 
                    subject.get("id") == group_id):
                    exists = True
                    break
            
            # Если не существует, добавляем
            if not exists:
                relationships["tuples"].append(new_tuple)
                # Сохраняем обновленные отношения
                self._save_relationships(relationships)
                print(f"DEBUG: Отношение добавлено в локальное хранилище")
            else:
                print(f"DEBUG: Отношение уже существует в локальном хранилище")
            
            # Проверяем, что отношение действительно было создано
            has_relation = self.check_relationship_exists(
                entity_type, entity_id, relation, "group", group_id, tenant_id
            )
            print(f"DEBUG: Проверка создания отношения: {has_relation}")
            
            if has_relation:
                return True, f"Роль {role} успешно назначена группе {group_id} для сущности {entity_type}:{entity_id}"
            else:
                return False, f"Ошибка при назначении роли: отношение не найдено после создания"
        else:
            return False, f"Ошибка при назначении роли: {result}"
    
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
    
    def get_group_roles(self, group_id: str, entity_type: str, entity_id: str, tenant_id: str = None) -> List[str]:
        """Получает список ролей группы для конкретного приложения."""
        tenant_id = tenant_id or self.default_tenant
        
        # Получаем все отношения
        success, relationships = self.get_relationships(tenant_id)
        if not success:
            return []
        
        # Ищем роли группы для указанного приложения
        group_roles = []
        for tuple_data in relationships.get("tuples", []):
            entity = tuple_data.get("entity", {})
            subject = tuple_data.get("subject", {})
            relation = tuple_data.get("relation", "")
            
            # Проверяем, что это отношение между приложением и группой
            if (entity.get("type") == entity_type and 
                entity.get("id") == entity_id and
                subject.get("type") == "group" and
                subject.get("id") == group_id):
                
                group_roles.append(relation)
        
        return group_roles
    
    def check_role_permission(self, entity_type: str, entity_id: str, permission: str, role: str, 
                             tenant_id: str = None, schema_version: str = None) -> bool:
        """Проверяет, дает ли указанная роль доступ к определенному действию."""
        # Получаем текущую схему для анализа правил
        from .schema_model import SchemaModel
        schema_model = SchemaModel()
        
        success, schema = schema_model.get_current_schema(tenant_id, schema_version)
        if not success or not schema:
            return False
        
        # Анализируем схему для поиска правила
        entities_info = schema_model.extract_entities_info(schema)
        
        # Проверяем, существует ли сущность и действие
        if entity_type not in entities_info:
            return False
        
        entity_def = entities_info[entity_type].get("definition", {})
        actions = entity_def.get("actions", {})
        
        # Проверяем действие
        if permission not in actions:
            return False
        
        # Анализируем правило для действия
        permission_rule = actions.get(permission, {}).get("rewrite", "")
        
        # Простая проверка: содержит ли правило имя роли
        return role in permission_rule 