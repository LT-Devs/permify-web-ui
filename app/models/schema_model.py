from .base_model import BaseModel
from typing import Dict, Any, List, Optional, Tuple, Union
import os
import tempfile

class SchemaModel(BaseModel):
    """Модель для работы со схемами Permify."""
    
    def get_schema_list(self, tenant_id: str = None) -> Tuple[bool, Any]:
        """Получает список всех схем."""
        tenant_id = tenant_id or self.default_tenant
        
        endpoint = f"/v1/tenants/{tenant_id}/schemas/list"
        data = {
            "page_size": 50,
            "continuous_token": ""
        }
        
        success, result = self.make_api_request(endpoint, data)
        
        # Обработка случая, когда схема не найдена (404)
        if not success and "ERROR_CODE_SCHEMA_NOT_FOUND" in str(result):
            # Возвращаем пустой список схем вместо ошибки
            return True, {"schemas": []}
        
        return success, result
    
    def get_current_schema(self, tenant_id: str = None, schema_version: str = None) -> Tuple[bool, Any]:
        """Получает текущую или указанную версию схемы. Создает схему, если она не существует."""
        tenant_id = tenant_id or self.default_tenant
        
        # Сначала получаем список схем
        success, schemas_result = self.get_schema_list(tenant_id)
        if not success:
            return False, schemas_result
        
        schemas_list = schemas_result
        
        # Проверяем, есть ли схемы в списке
        if not schemas_list.get("schemas") or len(schemas_list["schemas"]) == 0:
            # Если схемы нет, создаем новую на основе существующих данных
            return self.create_default_schema(tenant_id)
        
        # Сортируем схемы по дате создания (новые сначала)
        sorted_schemas = sorted(schemas_list["schemas"], 
                              key=lambda x: x.get('created_at', ''), 
                              reverse=True)
        
        # Если указана конкретная версия, используем её
        if schema_version:
            # Находим схему с указанной версией
            target_schema = None
            for schema in sorted_schemas:
                if schema.get("version") == schema_version:
                    target_schema = schema
                    break
            
            if not target_schema:
                return False, f"Схема с версией {schema_version} не найдена"
                
            version_to_use = schema_version
        else:
            # Иначе используем самую новую версию (первую в отсортированном списке)
            version_to_use = sorted_schemas[0]["version"]
        
        # Теперь получаем детальную информацию о схеме
        endpoint = f"/v1/tenants/{tenant_id}/schemas/read"
        data = {
            "metadata": {
                "schema_version": version_to_use
            }
        }
        
        success, schema_result = self.make_api_request(endpoint, data)
        if not success:
            return False, schema_result
        
        # Добавляем версию схемы к результату
        schema_result["version"] = version_to_use
        # Добавляем список всех доступных версий
        schema_result["available_versions"] = [{"version": s["version"], "created_at": s["created_at"]} for s in sorted_schemas]
        
        return True, schema_result
    
    def create_default_schema(self, tenant_id: str = None) -> Tuple[bool, Any]:
        """Создает схему по умолчанию на основе существующих данных."""
        tenant_id = tenant_id or self.default_tenant
        
        # Загружаем отношения для анализа
        from .relationship_model import RelationshipModel
        relationship_model = RelationshipModel()
        success, relationships = relationship_model.get_relationships(tenant_id)
        
        if not success:
            return False, f"Не удалось получить отношения для создания схемы: {relationships}"
        
        # Анализируем отношения и создаем словарь сущностей
        entities = {}
        relations = {}
        
        # Добавляем базовые сущности
        entities["user"] = {"relations": [], "actions": []}
        
        # Собираем информацию из отношений
        for tuple_data in relationships.get("tuples", []):
            entity = tuple_data.get("entity", {})
            relation = tuple_data.get("relation", "")
            subject = tuple_data.get("subject", {})
            
            entity_type = entity.get("type")
            subject_type = subject.get("type")
            
            # Добавляем сущности, если их еще нет
            if entity_type not in entities:
                entities[entity_type] = {"relations": [], "actions": []}
            
            if subject_type not in entities:
                entities[subject_type] = {"relations": [], "actions": []}
            
            # Добавляем отношение, если его еще нет
            relation_key = f"{entity_type}_{relation}"
            if relation_key not in relations:
                relations[relation_key] = True
                # Добавляем отношение к сущности
                if relation not in entities[entity_type]["relations"]:
                    entities[entity_type]["relations"].append(relation)
        
        # Создаем схему на основе собранной информации
        schema_content = "// Автоматически сгенерированная схема\n\n"
        
        # Добавляем сущность пользователя
        schema_content += "entity user {}\n\n"
        
        # Добавляем остальные сущности
        for entity_name, entity_data in entities.items():
            if entity_name == "user":
                continue
                
            schema_content += f"entity {entity_name} {{\n"
            
            # Добавляем отношения
            for relation in entity_data["relations"]:
                schema_content += f"  relation {relation} @user\n"
            
            # Добавляем стандартные действия
            standard_actions = ["view", "edit", "create", "delete"]
            for action in standard_actions:
                if len(entity_data["relations"]) > 0:
                    # Используем первое отношение как стандартное для действий
                    first_relation = entity_data["relations"][0]
                    schema_content += f"  action {action} = {first_relation}\n"
            
            schema_content += "}\n\n"
        
        # Создаем схему
        success, result = self.create_schema(schema_content, tenant_id)
        
        if success:
            print(f"Схема успешно создана для tenant_id {tenant_id}")
            # Получаем созданную схему для возврата
            return self.get_current_schema(tenant_id)
        else:
            return False, f"Ошибка при создании схемы: {result}"
    
    def create_schema(self, schema_content: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Создает новую схему."""
        tenant_id = tenant_id or self.default_tenant
        
        # Отладочный вывод
        print(f"Создание схемы для tenant_id {tenant_id}:")
        print(f"Схема: {schema_content}")
        
        endpoint = f"/v1/tenants/{tenant_id}/schemas/write"
        data = {
            "schema": schema_content
        }
        
        success, result = self.make_api_request(endpoint, data)
        if success:
            return True, "Схема успешно создана"
        else:
            print(f"Ошибка создания схемы: {result}")
            return False, result
    
    def validate_schema(self, schema_content: str) -> Tuple[bool, str]:
        """Валидирует схему."""
        try:
            # Создаем временный файл для схемы
            with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.perm') as f:
                f.write(schema_content)
                temp_file = f.name
            
            # Пробуем использовать validate API
            endpoints = [
                f"/v1/schemas/validate",
                f"/v1/tenants/{self.default_tenant}/schemas/validate"
            ]
            
            for endpoint in endpoints:
                try:
                    success, result = self.make_api_request(endpoint, {"schema": schema_content})
                    if success:
                        os.unlink(temp_file)
                        return True, "Схема валидна"
                except Exception:
                    pass  # Пробуем следующий эндпоинт
            
            # Если API не работает, проводим базовую валидацию
            valid = True
            errors = []
            
            lines = schema_content.strip().split('\n')
            brackets_count = 0
            
            for i, line in enumerate(lines):
                line = line.strip()
                if not line or line.startswith('//'):
                    continue
                
                brackets_count += line.count('{') - line.count('}')
                
                if 'entity' in line and '{' not in line and i < len(lines) - 1 and '{' not in lines[i + 1]:
                    valid = False
                    errors.append(f"Строка {i+1}: Ожидается открывающая скобка {{ после объявления entity")
            
            if brackets_count != 0:
                valid = False
                errors.append(f"Несбалансированные скобки: {brackets_count}")
                
            # Удаляем временный файл
            os.unlink(temp_file)
            
            if valid:
                return True, "Схема прошла базовую валидацию"
            else:
                return False, "Ошибки в схеме: " + "; ".join(errors)
        
        except Exception as e:
            return False, f"Ошибка при валидации: {str(e)}"
    
    def extract_entities_info(self, schema: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Извлекает информацию о сущностях из схемы."""
        entities_info = {}
        
        if not isinstance(schema, dict) or "schema" not in schema:
            return entities_info
            
        entity_definitions = schema.get("schema", {}).get("entityDefinitions", {})
        
        for entity_name, entity_def in entity_definitions.items():
            entities_info[entity_name] = {
                "permissions": list(entity_def.get("permissions", {}).keys()),
                "relations": list(entity_def.get("relations", {}).keys()),
                "attributes": list(entity_def.get("attributes", {}).keys()),
                "definition": entity_def
            }
        
        return entities_info
        
    def generate_schema_from_ui_data(self, apps_data: Dict[str, Any], groups_data: Dict[str, Any]) -> str:
        """Генерирует схему на основе данных из UI."""
        schema_lines = ["entity user {}"]
        
        # Добавляем группы
        for group_id, group_info in groups_data.items():
            schema_lines.append(f"\nentity group {{\n  relation member @user\n}}")
        
        # Добавляем приложения
        for app_id, app_info in apps_data.items():
            app_name = app_info["name"]
            app_lines = [f"\nentity {app_name} {{"]
            
            # Добавляем отношения
            app_lines.append("  relation owner @user")
            app_lines.append("  relation editor @user")
            app_lines.append("  relation viewer @user")
            app_lines.append("  relation member @group")
            
            # Добавляем действия (permissions)
            for action in app_info.get("actions", []):
                action_name = action["name"]
                # Формируем правило действия в зависимости от разрешений
                rule = "owner"
                if action.get("editor_allowed", False):
                    rule += " or editor"
                if action.get("viewer_allowed", False):
                    rule += " or viewer"
                if action.get("group_allowed", False):
                    rule += " or member"
                
                app_lines.append(f"  action {action_name} = {rule}")
            
            app_lines.append("}")
            schema_lines.append("\n".join(app_lines))
        
        return "\n".join(schema_lines)

    def generate_and_apply_schema(self, tenant_id: str = None) -> Tuple[bool, Any]:
        """Генерирует и применяет схему на основе текущих данных приложений и ролей."""
        tenant_id = tenant_id or self.default_tenant
        
        try:
            # Загружаем данные приложений из модели приложений
            from .app_model import AppModel
            app_model = AppModel()
            apps = app_model.get_apps(tenant_id)
            
            # Загружаем данные групп
            from .group_model import GroupModel
            group_model = GroupModel()
            groups = group_model.get_groups(tenant_id)
            
            # Преобразуем список групп в словарь для удобства
            groups_dict = {group.get('id'): group for group in groups}
            
            # Генерируем новую схему
            schema_content = "// Автоматически сгенерированная схема\n\n"
            
            # Добавляем базовые сущности
            schema_content += "entity user {}\n\n"
            schema_content += "entity group {\n  relation member @user\n}\n\n"
            
            # Добавляем приложения
            for app in apps:
                if app.get('is_template', False):
                    continue  # Пропускаем шаблоны
                
                app_name = app.get('name')
                app_id = app.get('id')
                if not app_name or not app_id:
                    continue
                
                schema_content += f"entity {app_name} {{\n"
                
                # Добавляем стандартные отношения
                schema_content += "  relation owner @user\n"
                schema_content += "  relation editor @user\n"
                schema_content += "  relation viewer @user\n"
                schema_content += "  relation owner @group\n"  # Добавляем роли для групп
                schema_content += "  relation editor @group\n"
                schema_content += "  relation viewer @group\n"
                
                # Добавляем пользовательские отношения
                custom_relations = app.get('metadata', {}).get('custom_relations', [])
                for relation in custom_relations:
                    schema_content += f"  relation {relation} @user\n"
                    schema_content += f"  relation {relation} @group\n"  # Добавляем роли для групп
                
                # Пустая строка между отношениями и действиями
                schema_content += "\n"
                
                # Собираем правила для действий
                for action in app.get('actions', []):
                    action_name = action.get('name')
                    if not action_name:
                        continue
                    
                    # Формируем правило для действия
                    rule_parts = ["owner"]  # владелец всегда имеет все права
                    
                    # Добавляем стандартные роли
                    if action.get('editor_allowed', False):
                        rule_parts.append("editor")
                    if action.get('viewer_allowed', False):
                        rule_parts.append("viewer")
                    
                    # Добавляем пользовательские роли
                    for key, value in action.items():
                        if key.endswith("_allowed") and key not in ["editor_allowed", "viewer_allowed", "group_allowed"] and value:
                            relation = key.replace("_allowed", "")
                            if relation in custom_relations:
                                rule_parts.append(relation)
                    
                    # Объединяем части правила с "or"
                    rule = " or ".join(rule_parts)
                    schema_content += f"  action {action_name} = {rule}\n"
                
                # Закрываем блок приложения
                schema_content += "}\n\n"
            
            # Удаляем последнюю пустую строку, если нужно
            schema_content = schema_content.rstrip() + "\n"
            
            # Валидируем схему перед применением
            is_valid, validation_msg = self.validate_schema(schema_content)
            if not is_valid:
                return False, f"Ошибка валидации схемы: {validation_msg}"
            
            # Применяем новую схему
            success, result = self.create_schema(schema_content, tenant_id)
            if not success:
                return False, f"Ошибка при создании схемы: {result}"
            
            return True, "Схема успешно создана и применена"
        
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Ошибка при генерации и применении схемы: {str(e)}\n{error_details}")
            return False, f"Ошибка при генерации и применении схемы: {str(e)}"

    def update_schema_for_role(self, app_name: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Обновляет схему для добавления новой роли, более надежный метод."""
        tenant_id = tenant_id or self.default_tenant
        
        # Вместо поиска в существующей схеме, генерируем новую
        return self.generate_and_apply_schema(tenant_id) 