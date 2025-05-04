from .base_model import BaseModel
from .relationship_model import RelationshipModel
from .schema_model import SchemaModel
from typing import Dict, Any, List, Optional, Tuple, Union
import os
import json

class AppModel(BaseModel):
    """Модель для управления приложениями в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.relationship_model = RelationshipModel()
        self.schema_model = SchemaModel()
        self.apps_file = os.path.join(os.getcwd(), 'data', 'apps.json')
        
        # Создаем директорию data, если она не существует
        os.makedirs(os.path.dirname(self.apps_file), exist_ok=True)
    
    def _load_apps(self) -> List[Dict[str, Any]]:
        """Загружает список приложений из файла."""
        if not os.path.exists(self.apps_file):
            print(f"Файл приложений не найден: {self.apps_file}")
            return []
        
        try:
            with open(self.apps_file, 'r') as f:
                loaded_apps = json.load(f).get('apps', [])
                print(f"Загружено {len(loaded_apps)} приложений из {self.apps_file}")
                
                # Дополнительная обработка для совместимости с более старыми форматами
                for app in loaded_apps:
                    # Убедимся, что метаданные существуют и это словарь
                    if 'metadata' not in app:
                        app['metadata'] = {}
                        print(f"Добавлены пустые метаданные для {app.get('name')}:{app.get('id')}")
                    
                    # Если в метаданных нет custom_relations, но в приложении есть действия с custom_relations
                    if 'custom_relations' not in app.get('metadata', {}) and 'actions' in app:
                        app['metadata']['custom_relations'] = []
                        print(f"Инициализируем custom_relations для {app.get('name')}:{app.get('id')}")
                        
                        # Ищем пользовательские отношения в действиях
                        for action in app.get('actions', []):
                            for key in action.keys():
                                if key.endswith("_allowed") and key not in ["editor_allowed", "viewer_allowed", "group_allowed"]:
                                    relation = key.replace("_allowed", "")
                                    if relation not in app['metadata']['custom_relations']:
                                        app['metadata']['custom_relations'].append(relation)
                                        print(f"Добавлено отношение {relation} из действий для {app.get('name')}:{app.get('id')}")
                    elif 'custom_relations' in app.get('metadata', {}) and app['metadata']['custom_relations']:
                        print(f"Загружены пользовательские отношения для {app.get('name')}:{app.get('id')}: {app['metadata']['custom_relations']}")
                
                return loaded_apps
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"Ошибка при загрузке приложений: {str(e)}")
            return []
    
    def _save_apps(self, apps: List[Dict[str, Any]]) -> bool:
        """Сохраняет список приложений в файл."""
        try:
            # Сохраняем приложения с поддержкой сложных объектов
            class AppEncoder(json.JSONEncoder):
                def default(self, obj):
                    if isinstance(obj, (dict, list, str, int, float, bool, type(None))):
                        return obj
                    return str(obj)
            
            # Обработка перед сохранением: убедимся, что все нужные поля присутствуют
            for app in apps:
                # Обработка метаданных
                if 'metadata' not in app:
                    app['metadata'] = {}
                
                # Проверяем наличие пользовательских отношений в метаданных
                if 'custom_relations' not in app['metadata']:
                    app['metadata']['custom_relations'] = []
                    
                    # Ищем пользовательские отношения в действиях
                    for action in app.get('actions', []):
                        for key in action.keys():
                            if key.endswith("_allowed") and key not in ["editor_allowed", "viewer_allowed", "group_allowed"]:
                                relation = key.replace("_allowed", "")
                                if relation not in app['metadata']['custom_relations']:
                                    app['metadata']['custom_relations'].append(relation)
                
                # Дополнительное логирование
                if 'custom_relations' in app['metadata'] and app['metadata']['custom_relations']:
                    print(f"Сохраняем пользовательские отношения для {app.get('name')}:{app.get('id')}: {app['metadata']['custom_relations']}")
            
            with open(self.apps_file, 'w') as f:
                json.dump({'apps': apps}, f, indent=2, cls=AppEncoder)
            
            # Проверяем, что данные записались корректно
            if os.path.exists(self.apps_file):
                with open(self.apps_file, 'r') as f:
                    try:
                        saved_data = json.load(f)
                        print(f"Данные успешно сохранены в {self.apps_file}")
                        return True
                    except json.JSONDecodeError as e:
                        print(f"Ошибка проверки сохраненного файла: {str(e)}")
                        return False
            return True
        except Exception as e:
            print(f"Ошибка при сохранении приложений: {str(e)}")
            return False
    
    def get_apps(self, tenant_id: str = None) -> List[Dict[str, Any]]:
        """Получает список приложений из хранилища и дополняет данными из схемы и отношений."""
        tenant_id = tenant_id or self.default_tenant
        
        # Загружаем приложения из файла
        stored_apps = self._load_apps()
        
        # Сначала собираем все пользовательские отношения из всех приложений
        all_custom_relations = set()
        for app in stored_apps:
            if 'metadata' in app and 'custom_relations' in app.get('metadata', {}):
                for relation in app.get('metadata', {}).get('custom_relations', []):
                    all_custom_relations.add(relation)
        
        apps_dict = {f"{app.get('name')}:{app.get('id')}": app for app in stored_apps}
        
        # Получаем информацию из схемы и отношений
        # Получаем текущую схему, чтобы найти все сущности, которые могут быть приложениями
        success, schema_result = self.schema_model.get_current_schema(tenant_id)
        if success and isinstance(schema_result, dict):
            # Извлекаем информацию о сущностях
            entities_info = self.schema_model.extract_entities_info(schema_result)
            
            # Фильтруем сущности, считая приложениями те, у которых есть
            # отношения owner, editor, viewer или permission/action (пропускаем user и group)
            for entity_name, entity_info in entities_info.items():
                if entity_name in ["user", "group"]:
                    continue
                    
                relations = entity_info.get("relations", [])
                permissions = entity_info.get("permissions", [])
                
                # Проверяем, есть ли нужные отношения или разрешения
                has_app_relations = any(rel in relations for rel in ["owner", "editor", "viewer", "member"])
                
                if has_app_relations or permissions:
                    # Добавляем тип приложения в словарь, если его еще нет
                    app_type_key = f"{entity_name}:"
                    if app_type_key not in apps_dict:
                        apps_dict[app_type_key] = {
                            "name": entity_name,
                            "id": "",
                            "display_name": entity_name.capitalize(),
                            "actions": [{"name": perm, "description": f"Разрешение {perm}"} for perm in permissions],
                            "users": [],
                            "groups": [],
                            "is_template": True
                        }
                    # Обновляем список действий для существующего типа
                    else:
                        apps_dict[app_type_key]["actions"] = [{"name": perm, "description": f"Разрешение {perm}"} for perm in permissions]
        
        # Дополняем информацию из отношений
        success, relationships = self.relationship_model.get_relationships(tenant_id)
        if success:
            # Обрабатываем отношения из Permify
            for tuple_data in relationships.get("tuples", []):
                entity = tuple_data.get("entity", {})
                subject = tuple_data.get("subject", {})
                relation = tuple_data.get("relation", "")
                
                entity_type = entity.get("type")
                entity_id = entity.get("id")
                
                # Пропускаем типы, которые не являются приложениями
                if entity_type in ["user", "group"]:
                    continue
                
                # Создаем ID для этого экземпляра приложения, если его еще нет
                app_instance_id = f"{entity_type}:{entity_id}"
                
                if app_instance_id not in apps_dict:
                    # Проверяем, есть ли шаблон для этого типа приложения
                    template_key = f"{entity_type}:"
                    template = apps_dict.get(template_key, {})
                    
                    # Если шаблона нет, создаем базовый шаблон
                    if not template:
                        template = {
                            "name": entity_type,
                            "id": "",
                            "display_name": entity_type.capitalize(),
                            "actions": [],
                            "is_template": True
                        }
                    
                    # Создаем новый экземпляр приложения
                    apps_dict[app_instance_id] = {
                        "id": entity_id,
                        "name": entity_type,
                        "display_name": template.get("display_name", entity_type.capitalize()),
                        "actions": template.get("actions", []),
                        "users": [],
                        "groups": [],
                        "metadata": {"custom_relations": []}
                    }
                
                # Добавляем пользователя с его ролью (включая стандартные и пользовательские роли)
                if subject.get("type") == "user":
                    user_id = subject.get("id")
                    # Проверяем, есть ли уже этот пользователь в списке
                    existing_user = next((u for u in apps_dict[app_instance_id]["users"] 
                                        if u.get("user_id") == user_id and u.get("role") == relation), None)
                    
                    if not existing_user:
                        apps_dict[app_instance_id]["users"].append({
                            "user_id": user_id,
                            "role": relation
                        })
                        
                        # Если это пользовательская роль (не стандартная), добавляем её в список
                        if relation not in ["owner", "editor", "viewer"] and 'metadata' in apps_dict[app_instance_id]:
                            if 'custom_relations' not in apps_dict[app_instance_id]['metadata']:
                                apps_dict[app_instance_id]['metadata']['custom_relations'] = []
                            
                            if relation not in apps_dict[app_instance_id]['metadata']['custom_relations']:
                                apps_dict[app_instance_id]['metadata']['custom_relations'].append(relation)
                
                # Добавляем группу
                elif relation == "member" and subject.get("type") == "group":
                    group_id = subject.get("id")
                    if group_id not in apps_dict[app_instance_id]["groups"]:
                        apps_dict[app_instance_id]["groups"].append(group_id)
        
        # Преобразуем словарь в список для вывода
        apps_list = list(apps_dict.values())
        
        # Сохраняем обновленный список в файл
        self._save_apps(apps_list)
        
        return apps_list
    
    def create_app(self, app_name: str, app_id: str, actions: List[Dict[str, Any]], tenant_id: str = None, metadata: Dict = None) -> Tuple[bool, str]:
        """Создает новое приложение (через обновление схемы и создание отношений)."""
        tenant_id = tenant_id or self.default_tenant
        metadata = metadata or {}
        
        # Проверяем, что имя и ID соответствуют требованиям
        if not app_name.isalnum():
            return False, "Название объекта должно содержать только буквы и цифры без пробелов"
        
        # Проверяем действия
        if not actions:
            return False, "Необходимо добавить хотя бы одно действие"
        
        for action in actions:
            if not action["name"].isalnum():
                return False, f"Название действия должно содержать только буквы и цифры: {action['name']}"
        
        # Сначала создаем запись в локальной БД
        stored_apps = self._load_apps()
        
        # Проверяем, существует ли уже приложение с таким именем и ID
        for app in stored_apps:
            if app.get('name') == app_name and app.get('id') == app_id:
                return False, f"Объект {app_name} с ID {app_id} уже существует"
        
        # Создаем новое приложение
        new_app = {
            "name": app_name,
            "id": app_id,
            "display_name": app_name.capitalize(),
            "actions": [{"name": action["name"], "description": f"Действие {action['name']}", 
                        "editor_allowed": action.get("editor_allowed", False),
                        "viewer_allowed": action.get("viewer_allowed", False),
                        "group_allowed": action.get("group_allowed", False)} 
                       for action in actions],
            "users": [],
            "groups": [],
            "metadata": metadata
        }
        
        # Добавляем в список и сохраняем
        stored_apps.append(new_app)
        if not self._save_apps(stored_apps):
            return False, "Ошибка при сохранении приложения в базу данных"
        
        try:
            # Принудительно обновляем схему
            self.force_rebuild_schema(tenant_id)
            
            return True, f"Приложение {app_name} успешно создано"
        except Exception as e:
            # В случае любой ошибки, мы все равно сохранили приложение в БД
            return True, f"Приложение сохранено в локальной БД, но возникла ошибка при работе с Permify: {str(e)}"
    
    def update_app(self, app_type: str, app_id: str, actions: List[Dict[str, Any]], tenant_id: str = None, metadata: Dict = None) -> Tuple[bool, str]:
        """Обновляет существующее приложение и его действия."""
        tenant_id = tenant_id or self.default_tenant
        metadata = metadata or {}
        
        # Собираем имена действий для дальнейшего обновления схемы
        action_names = [action["name"] for action in actions]
        custom_relations = set()
        
        # Ищем приложение для обновления
        app_found = False
        stored_apps = self._load_apps()
        
        for app in stored_apps:
            if app.get('name') == app_type and app.get('id') == app_id:
                app_found = True
                
                # Обновляем действия
                app['actions'] = [{"name": action["name"], "description": f"Действие {action['name']}", 
                                 "editor_allowed": action.get("editor_allowed", False),
                                 "viewer_allowed": action.get("viewer_allowed", False),
                                 "group_allowed": action.get("group_allowed", False)}
                                for action in actions]
                
                # Обрабатываем пользовательские свойства действий и собираем пользовательские отношения
                if 'metadata' in app and 'custom_relations' in app['metadata']:
                    for rel in app['metadata']['custom_relations']:
                        custom_relations.add(rel)
                
                for i, action in enumerate(actions):
                    for key, value in action.items():
                        if key.endswith("_allowed") and key not in ["editor_allowed", "viewer_allowed", "group_allowed"]:
                            app['actions'][i][key] = value
                            # Добавляем пользовательское отношение в список
                            relation = key.replace("_allowed", "")
                            custom_relations.add(relation)
                
                # Обновляем метаданные
                if 'metadata' not in app:
                    app["metadata"] = {}
                
                # Объединяем существующие custom_relations с новыми из metadata
                if 'custom_relations' in metadata:
                    for rel in metadata['custom_relations']:
                        custom_relations.add(rel)
                
                # Сохраняем обновленный список пользовательских отношений
                app["metadata"]["custom_relations"] = list(custom_relations)
                
                # Добавляем другие метаданные, если они есть
                for key, value in metadata.items():
                    if key != 'custom_relations':
                        app["metadata"][key] = value
                
                break
        
        if not app_found:
            return False, f"Приложение {app_type} с ID {app_id} не найдено"
        
        # Сохраняем обновленные приложения
        if not self._save_apps(stored_apps):
            return False, "Ошибка при сохранении изменений в базу данных"
        
        try:
            # Всегда обновляем схему после изменения приложения
            self.force_rebuild_schema(tenant_id)
            
            return True, f"Приложение {app_type} успешно обновлено"
        except Exception as e:
            # В случае любой ошибки при обновлении схемы, мы все равно сохранили изменения в БД
            return True, f"Приложение обновлено в локальной БД, но возникла ошибка при обновлении схемы: {str(e)}"

    def update_schema_for_app(self, app_name: str, actions: List[str], custom_relations: List[str], tenant_id: str = None) -> Tuple[bool, str]:
        """Обновляет схему с новыми действиями и отношениями для приложения."""
        tenant_id = tenant_id or self.default_tenant
        
        # Получаем текущую схему
        success, schema_result = self.schema_model.get_current_schema(tenant_id)
        if not success:
            return False, f"Не удалось получить схему: {schema_result}"
        
        # Проверяем, есть ли сущность для приложения в схеме
        entity_definitions = schema_result.get("schema", {}).get("entity_definitions", {})
        app_entity = entity_definitions.get(app_name, {})
        
        # Если сущности нет, создаем новую схему
        if not app_entity:
            schema_string = schema_result.get("schema_string", "")
            new_entity = f"\nentity {app_name} {{\n"
            new_entity += "  relation owner @user\n"
            new_entity += "  relation editor @user\n"
            new_entity += "  relation viewer @user\n"
            new_entity += "  relation member @group\n"
            
            # Добавляем пользовательские отношения
            for relation in custom_relations:
                new_entity += f"  relation {relation} @user\n"
            
            new_entity += "\n"
            
            # Добавляем действия
            for action in actions:
                rule = "owner"
                if action in ["view", "read"]:
                    rule = "owner or editor or viewer"
                elif action in ["edit", "update"]:
                    rule = "owner or editor"
                
                # Если это действие export и есть роль exporter, добавляем её
                if action == "export" and "exporter" in custom_relations:
                    rule += " or exporter"
                
                new_entity += f"  action {action} = {rule}\n"
            
            new_entity += "}\n"
            
            # Добавляем новую сущность в схему
            updated_schema = schema_string + new_entity
            
            # Создаем новую схему
            return self.schema_model.create_schema(updated_schema, tenant_id)
        
        # Если сущность уже есть, обновляем её
        schema_string = schema_result.get("schema_string", "")
        if not schema_string:
            return False, "Не удалось получить строковое представление схемы"
        
        # Разбиваем схему на строки
        lines = schema_string.split('\n')
        entity_start = -1
        entity_end = -1
        
        # Ищем блок сущности
        for i, line in enumerate(lines):
            line_stripped = line.strip()
            if line_stripped == f"entity {app_name} {{":
                entity_start = i
            elif entity_start != -1 and line_stripped == "}":
                entity_end = i
                break
        
        if entity_start == -1 or entity_end == -1:
            return False, f"Не удалось найти блок сущности {app_name} в схеме"
        
        # Формируем список текущих отношений и действий
        current_relations = set()
        current_actions = set()
        
        for i in range(entity_start + 1, entity_end):
            line = lines[i].strip()
            if line.startswith("relation"):
                parts = line.split()
                if len(parts) > 1:
                    relation = parts[1]
                    current_relations.add(relation)
            elif line.startswith("action"):
                parts = line.split()
                if len(parts) > 1:
                    action = parts[1]
                    current_actions.add(action)
        
        # Обновляем схему с новыми отношениями
        insert_index = entity_start + 1
        for relation in custom_relations:
            if relation not in current_relations:
                indentation = "  "  # Стандартный отступ в схеме
                new_relation_line = f"{indentation}relation {relation} @user"
                lines.insert(insert_index, new_relation_line)
                insert_index += 1
                entity_end += 1  # Увеличиваем индекс конца сущности
        
        # Обновляем схему с новыми действиями
        for action in actions:
            if action not in current_actions:
                rule = "owner"
                if action in ["view", "read"]:
                    rule = "owner or editor or viewer"
                elif action in ["edit", "update"]:
                    rule = "owner or editor"
                
                # Если это действие export и есть роль exporter, добавляем её
                if action == "export" and "exporter" in custom_relations:
                    rule += " or exporter"
                
                indentation = "  "  # Стандартный отступ в схеме
                new_action_line = f"{indentation}action {action} = {rule}"
                lines.insert(entity_end, new_action_line)
                entity_end += 1  # Увеличиваем индекс конца сущности
        
        # Собираем обновленную схему
        updated_schema = '\n'.join(lines)
        
        # Создаем новую схему
        success, result = self.schema_model.create_schema(updated_schema, tenant_id)
        if success:
            return True, "Схема успешно обновлена"
        else:
            return False, f"Ошибка при обновлении схемы: {result}"
    
    def assign_user_to_app(self, app_name: str, app_id: str, user_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает пользователю роль в приложении."""
        success, result = self.relationship_model.assign_user_to_app(app_name, app_id, user_id, role, tenant_id)
        
        if success:
            # Для любой роли (стандартной или пользовательской) обновляем схему
            # Это гарантирует, что схема всегда будет актуальной
            tenant_id = tenant_id or self.default_tenant
            self.force_rebuild_schema(tenant_id)
        
        return success, result

    def update_schema_with_custom_role(self, app_name: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Обновляет схему с новой пользовательской ролью."""
        tenant_id = tenant_id or self.default_tenant
        
        # Используем новый API для обновления схемы
        return self.schema_model.update_schema_for_role(app_name, role, tenant_id)
    
    def force_rebuild_schema(self, tenant_id: str = None) -> Tuple[bool, str]:
        """Принудительно пересоздает схему на основе текущих данных."""
        tenant_id = tenant_id or self.default_tenant
        return self.schema_model.generate_and_apply_schema(tenant_id)
    
    def remove_user_from_app(self, app_name: str, app_id: str, user_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет роль пользователя в приложении."""
        return self.relationship_model.delete_relationship(app_name, app_id, role, "user", user_id, tenant_id)
    
    def assign_group_to_app(self, app_name: str, app_id: str, group_id: str, role: str = "viewer", tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает группу приложению с определенной ролью."""
        from app.models.group_model import GroupModel
        group_model = GroupModel()
        
        success, result = group_model.assign_role_to_group(group_id, app_name, app_id, role, tenant_id)
        
        if success:
            # После назначения группы обновляем схему
            tenant_id = tenant_id or self.default_tenant
            self.force_rebuild_schema(tenant_id)
        
        return success, result
    
    def remove_group_from_app(self, app_name: str, app_id: str, group_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет группу из приложения с определенной ролью."""
        from app.models.group_model import GroupModel
        group_model = GroupModel()
        
        return group_model.remove_role_from_group(group_id, app_name, app_id, role, tenant_id)
    
    def check_user_permission(self, app_name: str, app_id: str, user_id: str, action: str, tenant_id: str = None) -> Tuple[bool, Any]:
        """Проверяет разрешение пользователя на действие в приложении."""
        return self.relationship_model.check_permission(app_name, app_id, action, user_id, tenant_id)
    
    def get_all_custom_relations(self) -> List[str]:
        """Возвращает список всех пользовательских типов отношений из всех приложений."""
        # Загружаем приложения из файла
        stored_apps = self._load_apps()
        
        # Собираем все пользовательские отношения
        all_relations = []
        for app in stored_apps:
            if 'metadata' in app and 'custom_relations' in app.get('metadata', {}):
                for relation in app.get('metadata', {}).get('custom_relations', []):
                    if relation not in all_relations:
                        all_relations.append(relation)
        
        return all_relations
        
    def delete_app(self, app_type: str, app_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет приложение и все его отношения из системы."""
        tenant_id = tenant_id or self.default_tenant
        
        # Сначала удаляем приложение из хранилища
        apps = self._load_apps()
        app_key = f"{app_type}:{app_id}"
        
        # Фильтруем список приложений
        filtered_apps = [app for app in apps if not (app.get('name') == app_type and app.get('id') == app_id)]
        
        if len(filtered_apps) == len(apps):
            return False, f"Приложение {app_type}:{app_id} не найдено"
        
        # Сохраняем обновленный список приложений
        if not self._save_apps(filtered_apps):
            return False, f"Ошибка при удалении приложения {app_type}:{app_id}"
        
        # Получаем текущие отношения для нахождения всех связей приложения
        success, relationships = self.relationship_model.get_relationships(tenant_id)
        if not success:
            return True, f"Приложение {app_type}:{app_id} удалено, но не удалось получить отношения"
        
        # Собираем все отношения, где приложение является сущностью
        app_relationships = []
        for tuple_data in relationships.get("tuples", []):
            entity = tuple_data.get("entity", {})
            
            if entity.get("type") == app_type and entity.get("id") == app_id:
                subject = tuple_data.get("subject", {})
                relation = tuple_data.get("relation", "")
                
                app_relationships.append({
                    "entity_type": app_type,
                    "entity_id": app_id,
                    "relation": relation,
                    "subject_type": subject.get("type"),
                    "subject_id": subject.get("id")
                })
        
        # Удаляем все отношения приложения
        if app_relationships:
            deleted_count, failed_count, errors = self.relationship_model.delete_multiple_relationships(
                app_relationships, tenant_id
            )
            
            if failed_count > 0:
                return True, f"Приложение {app_type}:{app_id} удалено, но {failed_count} из {deleted_count + failed_count} отношений не удалены"
        
        return True, f"Приложение {app_type}:{app_id} и все его отношения успешно удалены" 