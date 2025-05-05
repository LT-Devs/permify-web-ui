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
        """Создает схему по умолчанию на основе существующих данных с поддержкой наследования прав через группы."""
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
        entities["group"] = {"relations": ["member", "admin"], "actions": []}
        
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
        
        # Добавляем сущность группы
        schema_content += "entity group {\n"
        schema_content += "  relation member @user\n"
        schema_content += "  relation admin @user\n"
        schema_content += "}\n\n"
        
        # Добавляем остальные сущности
        for entity_name, entity_data in entities.items():
            if entity_name in ["user", "group"]:
                continue
                
            schema_content += f"entity {entity_name} {{\n"
            
            # Добавляем отношения с пользователями
            user_relations = []
            for relation in entity_data["relations"]:
                if relation.startswith("group_"):
                    continue  # Пропускаем relations, которые уже имеют префикс group_
                    
                schema_content += f"  relation {relation} @user\n"
                user_relations.append(relation)
            
            # Добавляем отношения с группами (с префиксом group_)
            for relation in user_relations:
                if relation in ["owner", "editor", "viewer"]:
                    schema_content += f"  relation group_{relation} @group\n"
            
            # Добавляем стандартные действия
            standard_actions = ["view", "edit", "create", "delete"]
            for action in standard_actions:
                # Формируем правила доступа с учетом групп
                rule_parts = []
                
                # Прямой доступ через роли пользователя
                if "owner" in user_relations:
                    rule_parts.append("owner")
                
                if action in ["view"] and "viewer" in user_relations:
                    rule_parts.append("viewer")
                    
                if action in ["view", "edit"] and "editor" in user_relations:
                    rule_parts.append("editor")
                
                # Доступ через группы
                group_rule_parts = []
                if "owner" in user_relations:
                    group_rule_parts.append("group_owner.member")
                    
                if action in ["view"] and "viewer" in user_relations:
                    group_rule_parts.append("group_viewer.member")
                    
                if action in ["view", "edit"] and "editor" in user_relations:
                    group_rule_parts.append("group_editor.member")
                
                # Объединяем правила
                all_rule_parts = rule_parts + group_rule_parts
                
                if all_rule_parts:
                    rule = " or ".join(all_rule_parts)
                    schema_content += f"  action {action} = {rule}\n"
            
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
        
    def generate_schema_from_ui_data(self, apps_data: List[Dict[str, Any]], groups_data: Dict[str, Any]) -> str:
        """Генерирует схему на основе данных из UI с корректной передачей прав от групп к пользователям."""
        schema_lines = []
        
        # Добавляем базового пользователя
        schema_lines.append("// Автоматически сгенерированная схема\n")
        schema_lines.append("// Базовая сущность пользователя")
        schema_lines.append("entity user {}")
        
        # Добавляем группы с правильной связью с пользователями
        schema_lines.append("\n// Группы пользователей")
        if groups_data:
            schema_lines.append("entity group {")
            schema_lines.append("  // Отношение между группой и её участниками")
            schema_lines.append("  relation member @user")
            schema_lines.append("  relation admin @user")
            schema_lines.append("}")
        else:
            # Если групп нет, всё равно создаем базовую сущность группы
            schema_lines.append("entity group {")
            schema_lines.append("  relation member @user")
            schema_lines.append("}")
        
        # Добавляем приложения с правильной моделью наследования прав
        # Проверяем, является ли apps_data списком или словарем
        if isinstance(apps_data, list):
            # Обрабатываем список приложений
            for app_info in apps_data:
                if not app_info.get("name"):
                    continue  # Пропускаем приложения без имени
                    
                app_name = app_info.get("name")
                schema_lines.append(f"\n// Приложение {app_name}")
                schema_lines.append(f"entity {app_name} {{")
                
                # Добавляем отношения с пользователями напрямую
                schema_lines.append("  // Прямые отношения с пользователями")
                schema_lines.append("  relation owner @user")
                schema_lines.append("  relation editor @user")
                schema_lines.append("  relation viewer @user")
                
                # Добавляем кастомные роли из метаданных
                custom_relations = []
                if 'metadata' in app_info and 'custom_relations' in app_info.get('metadata', {}):
                    custom_relations = app_info.get('metadata', {}).get('custom_relations', [])
                    
                if custom_relations:
                    schema_lines.append("\n  // Кастомные роли для пользователей")
                    for relation in custom_relations:
                        schema_lines.append(f"  relation {relation} @user")
                
                # Добавляем отношения с группами
                schema_lines.append("\n  // Отношения с группами")
                schema_lines.append("  relation group_owner @group")
                schema_lines.append("  relation group_editor @group")
                schema_lines.append("  relation group_viewer @group")
                
                # Добавляем отношения group_ для кастомных ролей
                if custom_relations:
                    schema_lines.append("\n  // Кастомные роли для групп")
                    for relation in custom_relations:
                        schema_lines.append(f"  relation group_{relation} @group")
                
                schema_lines.append("\n  // Действия (permissions) с учетом иерархии групп")
                
                # Добавляем действия с учетом прав групп
                for action in app_info.get("actions", []):
                    action_name = action.get("name")
                    if not action_name:
                        continue  # Пропускаем действия без имени
                        
                    # Формируем правило действия с учетом наследования прав от групп к пользователям
                    rule_parts = ["owner"]
                    
                    if action.get("editor_allowed", False):
                        rule_parts.append("editor")
                    
                    if action.get("viewer_allowed", False):
                        rule_parts.append("viewer")
                    
                    # Добавляем кастомные роли с соответствующими правами
                    for custom_role in custom_relations:
                        if action.get(f"{custom_role}_allowed", False):
                            rule_parts.append(custom_role)
                    
                    # Добавляем доступ через группы (группа → участник группы)
                    group_rules = []
                    if action.get("editor_allowed", False) or action.get("group_allowed", False):
                        group_rules.append("group_editor.member")
                    
                    if action.get("viewer_allowed", False) or action.get("group_allowed", False):
                        group_rules.append("group_viewer.member")
                    
                    # Добавляем группы с кастомными ролями
                    for custom_role in custom_relations:
                        if action.get(f"{custom_role}_allowed", False) or action.get("group_allowed", False):
                            group_rules.append(f"group_{custom_role}.member")
                    
                    # Владельцы групп всегда имеют все права
                    group_rules.append("group_owner.member")
                    
                    # Объединяем правила
                    all_rules = rule_parts + group_rules
                    rule = " or ".join(all_rules)
                    
                    schema_lines.append(f"  action {action_name} = {rule}")
                
                schema_lines.append("}")
        
        # Если нет приложений, добавляем базовое application
        if not apps_data:
            schema_lines.append("\n// Базовое приложение")
            schema_lines.append("entity application {")
            schema_lines.append("  // Прямые отношения с пользователями")
            schema_lines.append("  relation owner @user")
            schema_lines.append("  relation editor @user")
            schema_lines.append("  relation viewer @user")
            
            schema_lines.append("\n  // Отношения с группами")
            schema_lines.append("  relation group_owner @group")
            schema_lines.append("  relation group_editor @group")
            schema_lines.append("  relation group_viewer @group")
            
            schema_lines.append("\n  // Стандартные действия")
            schema_lines.append("  action view = owner or editor or viewer or group_owner.member or group_editor.member or group_viewer.member")
            schema_lines.append("  action edit = owner or editor or group_owner.member or group_editor.member")
            schema_lines.append("  action delete = owner or group_owner.member")
            schema_lines.append("  action create = owner or group_owner.member")
            schema_lines.append("}")
        
        return "\n".join(schema_lines)

    def generate_and_apply_schema(self, tenant_id: str = None) -> Tuple[bool, str]:
        """Генерирует и применяет схему на основе существующих данных."""
        tenant_id = tenant_id or self.default_tenant
        
        # Получаем данные о приложениях
        from .app_model import AppModel
        app_model = AppModel()
        apps_data = app_model.get_apps(tenant_id)
        
        # Получаем данные о группах
        from .group_model import GroupModel
        group_model = GroupModel()
        groups_data = group_model.get_groups(tenant_id)
        
        try:
            # Генерируем схему на основе данных
            schema_content = self.generate_schema_from_ui_data(apps_data, groups_data)
            
            if not schema_content:
                # Если нет данных для генерации, создаем минимальную схему
                schema_content = """// Базовая схема Permify
entity user {}

entity group {
    relation member @user
}

entity application {
    relation owner @user @group
    relation editor @user @group
    relation viewer @user @group
    
    action view = owner or editor or viewer
    action edit = owner or editor
    action delete = owner or group_owner.member
    action create = owner or group_owner.member
}
"""
            
            # Создаем схему
            success, result = self.create_schema(schema_content, tenant_id)
            
            if success:
                return True, "Схема успешно создана и применена"
            else:
                return False, f"Ошибка при создании схемы: {result}"
        except Exception as e:
            import traceback
            return False, f"Ошибка при генерации схемы: {str(e)}\n{traceback.format_exc()}"

    def update_schema_for_role(self, app_name: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Обновляет схему для добавления новой роли, более надежный метод."""
        tenant_id = tenant_id or self.default_tenant
        
        # Вместо поиска в существующей схеме, генерируем новую
        return self.generate_and_apply_schema(tenant_id)

    def get_generated_schema_text(self, tenant_id: str = None) -> Tuple[bool, str]:
        """Возвращает текст генерируемой схемы без её создания (для предпросмотра)."""
        tenant_id = tenant_id or self.default_tenant
        
        try:
            # Получаем данные о приложениях
            from .app_model import AppModel
            app_model = AppModel()
            apps_data = app_model.get_apps(tenant_id)
            
            # Получаем данные о группах
            from .group_model import GroupModel
            group_model = GroupModel()
            groups_data = group_model.get_groups(tenant_id)
            
            # Генерируем схему на основе данных
            schema_content = self.generate_schema_from_ui_data(apps_data, groups_data)
            
            if not schema_content:
                # Если нет данных для генерации, используем минимальную схему
                schema_content = """// Базовая схема Permify
entity user {}

entity group {
    relation member @user
}

entity application {
    relation owner @user
    relation editor @user
    relation viewer @user
    
    relation group_owner @group
    relation group_editor @group
    relation group_viewer @group
    
    action view = owner or editor or viewer or group_owner.member or group_editor.member or group_viewer.member
    action edit = owner or editor or group_owner.member or group_editor.member
    action delete = owner or group_owner.member
    action create = owner or group_owner.member
}
"""
            
            return True, schema_content
        except Exception as e:
            import traceback
            return False, f"Ошибка при генерации схемы: {str(e)}\n{traceback.format_exc()}" 