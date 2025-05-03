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
        
        return self.make_api_request(endpoint, data)
    
    def get_current_schema(self, tenant_id: str = None, schema_version: str = None) -> Tuple[bool, Any]:
        """Получает текущую или указанную версию схемы."""
        tenant_id = tenant_id or self.default_tenant
        
        # Сначала получаем список схем
        success, schemas_result = self.get_schema_list(tenant_id)
        if not success:
            return False, schemas_result
        
        schemas_list = schemas_result
        
        # Проверяем, есть ли схемы в списке
        if not schemas_list.get("schemas") or len(schemas_list["schemas"]) == 0:
            return False, "Нет доступных схем"
        
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