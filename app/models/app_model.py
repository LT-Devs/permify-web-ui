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
            for tuple_data in relationships.get("tuples", []):
                entity = tuple_data.get("entity", {})
                subject = tuple_data.get("subject", {})
                relation = tuple_data.get("relation", "")
                
                entity_type = entity.get("type")
                entity_id = entity.get("id")
                
                # Пропускаем типы, которые не являются приложениями
                if entity_type in ["user", "group"] or f"{entity_type}:" not in apps_dict:
                    continue
                
                # Создаем ID для этого экземпляра приложения, если его еще нет
                app_instance_id = f"{entity_type}:{entity_id}"
                
                if app_instance_id not in apps_dict:
                    # Копируем данные из шаблона
                    template = apps_dict.get(f"{entity_type}:", {})
                    apps_dict[app_instance_id] = {
                        "id": entity_id,
                        "name": entity_type,
                        "display_name": template.get("display_name", entity_type.capitalize()),
                        "actions": template.get("actions", []),
                        "users": [],
                        "groups": []
                    }
                
                # Добавляем пользователя с его ролью
                if relation in ["owner", "editor", "viewer"] and subject.get("type") == "user":
                    user_id = subject.get("id")
                    # Проверяем, есть ли уже этот пользователь в списке
                    existing_user = next((u for u in apps_dict[app_instance_id]["users"] 
                                        if u.get("user_id") == user_id and u.get("role") == relation), None)
                    
                    if not existing_user:
                        apps_dict[app_instance_id]["users"].append({
                            "user_id": user_id,
                            "role": relation
                        })
                
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
            # Сначала получаем текущую схему
            success, schema_result = self.schema_model.get_current_schema(tenant_id)
            if not success:
                return True, "Приложение сохранено в локальной БД, но не удалось получить текущую схему Permify"
            
            # Проверяем, есть ли уже такое приложение в схеме
            entities_info = self.schema_model.extract_entities_info(schema_result)
            if app_name in entities_info:
                # Приложение уже есть в схеме, просто создаем связи
                return True, f"Приложение {app_name} сохранено локально и уже существует в схеме Permify"
            
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
            app_schema += "  relation member @group\n"
            
            # Добавляем пользовательские отношения, если они есть
            if "custom_relations" in metadata:
                for relation in metadata["custom_relations"]:
                    app_schema += f"  relation {relation} @user\n"
            
            app_schema += "\n"
            
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
                
                # Добавляем пользовательские отношения
                for key, value in action.items():
                    if key.endswith("_allowed") and key not in ["editor_allowed", "viewer_allowed", "group_allowed"] and value:
                        relation = key.replace("_allowed", "")
                        action_rule += f" or {relation}"
                
                app_schema += f"  action {action_name} = {action_rule}\n"
            
            app_schema += "}\n"
            
            # Объединяем схему
            new_schema = schema_content + app_schema
            
            # Валидируем новую схему
            is_valid, validation_msg = self.schema_model.validate_schema(new_schema)
            if not is_valid:
                return True, f"Приложение сохранено в локальной БД, но есть ошибка в схеме Permify: {validation_msg}"
            
            # Создаем новую схему
            success, result = self.schema_model.create_schema(new_schema, tenant_id)
            if not success:
                return True, f"Приложение сохранено в локальной БД, но возникла ошибка при обновлении схемы Permify: {result}"
            
            return True, f"Приложение {app_name} успешно создано"
        except Exception as e:
            # В случае любой ошибки, мы все равно сохранили приложение в БД
            return True, f"Приложение сохранено в локальной БД, но возникла ошибка при работе с Permify: {str(e)}"
    
    def update_app(self, app_type: str, app_id: str, actions: List[Dict[str, Any]], tenant_id: str = None, metadata: Dict = None) -> Tuple[bool, str]:
        """Обновляет существующее приложение и его действия."""
        tenant_id = tenant_id or self.default_tenant
        metadata = metadata or {}
        
        # Загружаем текущие приложения
        stored_apps = self._load_apps()
        
        # Ищем приложение для обновления
        app_found = False
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
                custom_relations = set()
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
            # Обновляем схему в Permify
            success, schema_result = self.schema_model.get_current_schema(tenant_id)
            if not success:
                return True, "Приложение обновлено в локальной БД, но не удалось получить текущую схему Permify"
            
            schema_content = schema_result.get("schema_string", "")
            if not schema_content:
                return True, "Приложение обновлено в локальной БД, но не удалось получить содержимое схемы Permify"
            
            # Разбираем схему на строки и находим блок приложения
            lines = schema_content.split('\n')
            app_start = -1
            app_end = -1
            
            for i, line in enumerate(lines):
                if line.strip() == f"entity {app_type} {{":
                    app_start = i
                elif app_start != -1 and line.strip() == "}":
                    app_end = i
                    break
            
            if app_start == -1 or app_end == -1:
                return True, f"Приложение обновлено в локальной БД, но не удалось найти блок приложения {app_type} в схеме Permify"
            
            # Собираем новый блок для приложения
            new_app_block = [f"entity {app_type} {{"]
            
            # Сохраняем отношения из текущего блока
            relations_added = set()
            for i in range(app_start + 1, app_end):
                line = lines[i].strip()
                if line.startswith("relation"):
                    new_app_block.append(f"  {line}")
                    parts = line.split()
                    if len(parts) >= 2:
                        relations_added.add(parts[1])
            
            # Добавляем стандартные отношения, если их нет
            standard_relations = {"owner @user", "editor @user", "viewer @user", "member @group"}
            for relation in standard_relations:
                relation_name = relation.split()[0]
                if relation_name not in relations_added:
                    new_app_block.append(f"  relation {relation}")
                    relations_added.add(relation_name)
            
            # Добавляем пользовательские отношения из метаданных
            if "custom_relations" in metadata:
                for relation in metadata["custom_relations"]:
                    if relation not in relations_added:
                        new_app_block.append(f"  relation {relation} @user")
                        relations_added.add(relation)
            
            new_app_block.append("")  # Пустая строка для отделения от действий
            
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
                
                # Добавляем пользовательские отношения
                for key, value in action.items():
                    if key.endswith("_allowed") and key not in ["editor_allowed", "viewer_allowed", "group_allowed"]:
                        relation = key.replace("_allowed", "")
                        action_rule += f" or {relation}"
                
                new_app_block.append(f"  action {action_name} = {action_rule}")
            
            new_app_block.append("}")
            
            # Объединяем схему
            new_lines = lines[:app_start] + new_app_block + lines[app_end+1:]
            new_schema = "\n".join(new_lines)
            
            # Валидируем новую схему
            is_valid, validation_msg = self.schema_model.validate_schema(new_schema)
            if not is_valid:
                return True, f"Приложение обновлено в локальной БД, но есть ошибка в схеме Permify: {validation_msg}"
            
            # Создаем новую схему
            success, result = self.schema_model.create_schema(new_schema, tenant_id)
            if not success:
                return True, f"Приложение обновлено в локальной БД, но возникла ошибка при обновлении схемы Permify: {result}"
            
            return True, f"Приложение {app_type} успешно обновлено"
        except Exception as e:
            # В случае любой ошибки, мы все равно сохранили изменения в БД
            return True, f"Приложение обновлено в локальной БД, но возникла ошибка при работе с Permify: {str(e)}"
    
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
    
    def get_all_custom_relations(self) -> List[str]:
        """Возвращает список всех пользовательских типов отношений из всех приложений."""
        stored_apps = self._load_apps()
        custom_relations = set()
        
        # Собираем пользовательские отношения из метаданных приложений
        for app in stored_apps:
            if 'metadata' in app and 'custom_relations' in app.get('metadata', {}):
                for relation in app.get('metadata', {}).get('custom_relations', []):
                    custom_relations.add(relation)
            
            # Также проверяем действия на наличие пользовательских отношений
            for action in app.get('actions', []):
                for key in action.keys():
                    if key.endswith("_allowed") and key not in ["editor_allowed", "viewer_allowed", "group_allowed"]:
                        relation = key.replace("_allowed", "")
                        custom_relations.add(relation)
        
        return list(custom_relations) 