from .base_model import BaseModel
from .relationship_model import RelationshipModel
from typing import Dict, Any, List, Optional, Tuple, Union
import os
import json

class GroupModel(BaseModel):
    """Модель для управления группами в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.relationship_model = RelationshipModel()
        self.groups_file = os.path.join(os.getcwd(), 'data', 'groups.json')
        
        # Создаем директорию data, если она не существует
        os.makedirs(os.path.dirname(self.groups_file), exist_ok=True)
    
    def _load_groups(self) -> List[Dict[str, Any]]:
        """Загружает список групп из файла."""
        if not os.path.exists(self.groups_file):
            return []
        
        try:
            with open(self.groups_file, 'r') as f:
                return json.load(f).get('groups', [])
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_groups(self, groups: List[Dict[str, Any]]) -> bool:
        """Сохраняет список групп в файл."""
        try:
            with open(self.groups_file, 'w') as f:
                json.dump({'groups': groups}, f, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении групп: {str(e)}")
            return False
    
    def get_groups(self, tenant_id: str = None) -> List[Dict[str, Any]]:
        """Получает список групп из хранилища и дополняет данными из отношений."""
        tenant_id = tenant_id or self.default_tenant
        
        # Загружаем группы из файла
        stored_groups = self._load_groups()
        groups_dict = {group.get('id'): group for group in stored_groups}
        
        # Получаем информацию из отношений
        success, relationships = self.relationship_model.get_relationships(tenant_id)
        
        if success:
            for tuple_data in relationships.get("tuples", []):
                entity = tuple_data.get("entity", {})
                subject = tuple_data.get("subject", {})
                relation = tuple_data.get("relation", "")
                
                # Если это группа как сущность
                if entity.get("type") == "group":
                    group_id = entity.get("id")
                    if group_id not in groups_dict:
                        groups_dict[group_id] = {
                            "id": group_id,
                            "name": f"Группа {group_id}",
                            "members": [],
                            "app_memberships": []
                        }
                    
                    # Если это отношение member с пользователем
                    if relation == "member" and subject.get("type") == "user":
                        user_id = subject.get("id")
                        if "members" not in groups_dict[group_id]:
                            groups_dict[group_id]["members"] = []
                        if user_id not in groups_dict[group_id]["members"]:
                            groups_dict[group_id]["members"].append(user_id)
                
                # Если это группа как субъект (для связей с приложениями)
                elif subject.get("type") == "group":
                    group_id = subject.get("id")
                    if group_id not in groups_dict:
                        groups_dict[group_id] = {
                            "id": group_id,
                            "name": f"Группа {group_id}",
                            "members": [],
                            "app_memberships": []
                        }
                    
                    # Проверяем роль группы в приложении
                    if relation.startswith("group_"):
                        app_type = entity.get("type")
                        app_id = entity.get("id")
                        role = relation.replace("group_", "")  # убираем префикс group_
                        
                        if "app_memberships" not in groups_dict[group_id]:
                            groups_dict[group_id]["app_memberships"] = []
                        
                        # Проверяем, нет ли уже такого членства
                        existing_membership = False
                        for membership in groups_dict[group_id].get("app_memberships", []):
                            if (membership.get("app_type") == app_type and 
                                membership.get("app_id") == app_id):
                                # Обновляем роль, если найдено существующее членство
                                membership["role"] = role
                                existing_membership = True
                                break
                        
                        if not existing_membership:
                            groups_dict[group_id]["app_memberships"].append({
                                "app_type": app_type,
                                "app_id": app_id,
                                "role": role
                            })
        
        return list(groups_dict.values())
    
    def create_group(self, group_id: str, name: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Создает новую группу и сохраняет в хранилище."""
        groups = self._load_groups()
        
        # Проверяем, существует ли уже группа с таким ID
        for group in groups:
            if group.get('id') == group_id:
                return False, f"Группа с ID {group_id} уже существует"
        
        # Создаем новую группу
        new_group = {
            "id": group_id,
            "name": name or f"Группа {group_id}",
            "members": [],
            "app_memberships": []
        }
        
        groups.append(new_group)
        
        # Сохраняем обновленный список групп
        if self._save_groups(groups):
            return True, f"Группа {group_id} создана"
        else:
            return False, "Ошибка при сохранении группы"
    
    def update_group(self, group_id: str, name: str) -> Tuple[bool, str]:
        """Обновляет информацию о группе."""
        groups = self._load_groups()
        
        for i, group in enumerate(groups):
            if group.get('id') == group_id:
                groups[i]['name'] = name
                if self._save_groups(groups):
                    return True, f"Информация о группе {group_id} обновлена"
                else:
                    return False, "Ошибка при сохранении группы"
        
        return False, f"Группа с ID {group_id} не найдена"
    
    def delete_group(self, group_id: str) -> Tuple[bool, str]:
        """Удаляет группу из хранилища."""
        groups = self._load_groups()
        
        groups = [group for group in groups if group.get('id') != group_id]
        
        if self._save_groups(groups):
            return True, f"Группа {group_id} удалена из системы"
        else:
            return False, "Ошибка при удалении группы"
            
    def delete_group_with_relations(self, group_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет группу и все ее отношения из системы."""
        tenant_id = tenant_id or self.default_tenant
        
        # Сначала удаляем группу из хранилища
        delete_success, delete_message = self.delete_group(group_id)
        if not delete_success:
            return delete_success, delete_message
        
        # Получаем текущие отношения для нахождения всех связей группы
        success, relationships = self.relationship_model.get_relationships(tenant_id)
        if not success:
            return True, f"Группа {group_id} удалена, но не удалось получить отношения"
        
        # Собираем все отношения, связанные с группой
        group_relationships = []
        for tuple_data in relationships.get("tuples", []):
            entity = tuple_data.get("entity", {})
            subject = tuple_data.get("subject", {})
            relation = tuple_data.get("relation", "")
            
            # Отношения, где группа - сущность (пользователи в группе)
            if entity.get("type") == "group" and entity.get("id") == group_id:
                group_relationships.append({
                    "entity_type": "group",
                    "entity_id": group_id,
                    "relation": relation,
                    "subject_type": subject.get("type"),
                    "subject_id": subject.get("id")
                })
            
            # Отношения, где группа - субъект (группа имеет роли в приложениях)
            elif subject.get("type") == "group" and subject.get("id") == group_id:
                group_relationships.append({
                    "entity_type": entity.get("type"),
                    "entity_id": entity.get("id"),
                    "relation": relation,
                    "subject_type": "group",
                    "subject_id": group_id
                })
        
        # Удаляем все отношения группы
        if group_relationships:
            deleted_count, failed_count, errors = self.relationship_model.delete_multiple_relationships(
                group_relationships, tenant_id
            )
            
            if failed_count > 0:
                return True, f"Группа {group_id} удалена, но {failed_count} из {deleted_count + failed_count} отношений не удалены"
        
        return True, f"Группа {group_id} и все её отношения успешно удалены"
    
    def add_user_to_group(self, group_id: str, user_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Добавляет пользователя в группу."""
        # Проверяем, существует ли группа
        groups = self._load_groups()
        group_exists = False
        
        for group in groups:
            if group.get('id') == group_id:
                group_exists = True
                break
        
        # Если группа не существует, создаем ее
        if not group_exists:
            self.create_group(group_id, f"Группа {group_id}")
        
        # Добавляем отношение в Permify
        return self.relationship_model.assign_user_to_group(group_id, user_id, tenant_id)
    
    def remove_user_from_group(self, group_id: str, user_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет пользователя из группы."""
        return self.relationship_model.delete_relationship("group", group_id, "member", "user", user_id, tenant_id)
    
    def assign_role_to_group(self, group_id: str, app_name: str, app_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает роль (право доступа) группе для приложения."""
        # Проверяем, существует ли группа
        groups = self._load_groups()
        group_exists = False
        
        for group in groups:
            if group.get('id') == group_id:
                group_exists = True
                break
        
        # Если группа не существует, создаем ее
        if not group_exists:
            self.create_group(group_id, f"Группа {group_id}")
        
        # Добавляем отношение в Permify
        return self.relationship_model.assign_role_to_group(group_id, app_name, app_id, role, tenant_id)
    
    def remove_role_from_group(self, group_id: str, app_type: str, app_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет роль группы из приложения."""
        return self.relationship_model.delete_relationship(app_type, app_id, role, "group", group_id, tenant_id)
    
    def remove_group_from_app(self, group_id: str, app_name: str, app_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет группу из приложения (удаляет отношение)."""
        # Используем префикс group_ для отношений группы
        group_role = f"group_{role}"
        
        # Удаляем отношение
        return self.relationship_model.delete_relationship(app_name, app_id, group_role, "group", group_id, tenant_id) 