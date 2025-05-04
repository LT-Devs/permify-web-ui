from .base_model import BaseModel
from .relationship_model import RelationshipModel
from typing import Dict, Any, List, Optional, Tuple, Union
import os
import json

class UserModel(BaseModel):
    """Модель для управления пользователями в упрощенном интерфейсе."""
    
    def __init__(self):
        super().__init__()
        self.relationship_model = RelationshipModel()
        self.users_file = os.path.join(os.getcwd(), 'data', 'users.json')
        
        # Создаем директорию data, если она не существует
        os.makedirs(os.path.dirname(self.users_file), exist_ok=True)
    
    def _load_users(self) -> List[Dict[str, Any]]:
        """Загружает список пользователей из файла."""
        if not os.path.exists(self.users_file):
            return []
        
        try:
            with open(self.users_file, 'r') as f:
                return json.load(f).get('users', [])
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _save_users(self, users: List[Dict[str, Any]]) -> bool:
        """Сохраняет список пользователей в файл."""
        try:
            with open(self.users_file, 'w') as f:
                json.dump({'users': users}, f, indent=2)
            return True
        except Exception as e:
            print(f"Ошибка при сохранении пользователей: {str(e)}")
            return False
    
    def get_users(self, tenant_id: str = None) -> List[Dict[str, Any]]:
        """Получает список пользователей из хранилища и дополняет данными из отношений."""
        tenant_id = tenant_id or self.default_tenant
        
        # Загружаем пользователей из файла
        stored_users = self._load_users()
        users_dict = {user.get('id'): user for user in stored_users}
        
        # Получаем информацию из отношений
        success, relationships = self.relationship_model.get_relationships(tenant_id)
        
        if success:
            for tuple_data in relationships.get("tuples", []):
                subject = tuple_data.get("subject", {})
                entity = tuple_data.get("entity", {})
                
                # Добавляем пользователей из субъектов
                if subject.get("type") == "user":
                    user_id = subject.get("id")
                    if user_id not in users_dict:
                        users_dict[user_id] = {
                            "id": user_id,
                            "name": f"Пользователь {user_id}",
                            "groups": [],
                            "app_roles": []
                        }
                    
                    # Если это связь с группой, добавляем группу пользователю
                    if entity.get("type") == "group" and tuple_data.get("relation") == "member":
                        group_id = entity.get("id")
                        if group_id not in users_dict[user_id].get("groups", []):
                            if "groups" not in users_dict[user_id]:
                                users_dict[user_id]["groups"] = []
                            users_dict[user_id]["groups"].append(group_id)
                    
                    # Если это связь с приложением, добавляем роль пользователю
                    else:
                        app_type = entity.get("type")
                        app_id = entity.get("id")
                        role = tuple_data.get("relation")
                        
                        if "app_roles" not in users_dict[user_id]:
                            users_dict[user_id]["app_roles"] = []
                        
                        # Проверяем, нет ли уже такой роли
                        existing_role = False
                        for app_role in users_dict[user_id]["app_roles"]:
                            if (app_role.get("app_type") == app_type and 
                                app_role.get("app_id") == app_id and 
                                app_role.get("role") == role):
                                existing_role = True
                                break
                        
                        if not existing_role:
                            users_dict[user_id]["app_roles"].append({
                                "app_type": app_type,
                                "app_id": app_id,
                                "role": role
                            })
        
        return list(users_dict.values())
    
    def create_user(self, user_id: str, name: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Создает нового пользователя и сохраняет в хранилище."""
        users = self._load_users()
        
        # Проверяем, существует ли уже пользователь с таким ID
        for user in users:
            if user.get('id') == user_id:
                return False, f"Пользователь с ID {user_id} уже существует"
        
        # Создаем нового пользователя
        new_user = {
            "id": user_id,
            "name": name or f"Пользователь {user_id}",
            "groups": [],
            "app_roles": []
        }
        
        users.append(new_user)
        
        # Сохраняем обновленный список пользователей
        if self._save_users(users):
            return True, f"Пользователь {user_id} добавлен в систему"
        else:
            return False, "Ошибка при сохранении пользователя"
    
    def update_user(self, user_id: str, name: str) -> Tuple[bool, str]:
        """Обновляет информацию о пользователе."""
        users = self._load_users()
        
        for i, user in enumerate(users):
            if user.get('id') == user_id:
                users[i]['name'] = name
                if self._save_users(users):
                    return True, f"Информация о пользователе {user_id} обновлена"
                else:
                    return False, "Ошибка при сохранении пользователя"
        
        return False, f"Пользователь с ID {user_id} не найден"
    
    def delete_user(self, user_id: str) -> Tuple[bool, str]:
        """Удаляет пользователя из хранилища."""
        users = self._load_users()
        
        users = [user for user in users if user.get('id') != user_id]
        
        if self._save_users(users):
            return True, f"Пользователь {user_id} удален из системы"
        else:
            return False, "Ошибка при удалении пользователя"
    
    def delete_user_with_relations(self, user_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет пользователя и все его отношения из системы."""
        tenant_id = tenant_id or self.default_tenant
        
        # Сначала удаляем пользователя из хранилища
        delete_success, delete_message = self.delete_user(user_id)
        if not delete_success:
            return delete_success, delete_message
        
        # Получаем текущие отношения для нахождения всех связей пользователя
        success, relationships = self.relationship_model.get_relationships(tenant_id)
        if not success:
            return True, f"Пользователь {user_id} удален, но не удалось получить отношения"
        
        # Собираем все отношения, где пользователь является субъектом
        user_relationships = []
        for tuple_data in relationships.get("tuples", []):
            subject = tuple_data.get("subject", {})
            
            if subject.get("type") == "user" and subject.get("id") == user_id:
                entity = tuple_data.get("entity", {})
                relation = tuple_data.get("relation", "")
                
                user_relationships.append({
                    "entity_type": entity.get("type"),
                    "entity_id": entity.get("id"),
                    "relation": relation,
                    "subject_type": "user",
                    "subject_id": user_id
                })
        
        # Удаляем все отношения пользователя
        if user_relationships:
            deleted_count, failed_count, errors = self.relationship_model.delete_multiple_relationships(
                user_relationships, tenant_id
            )
            
            if failed_count > 0:
                return True, f"Пользователь {user_id} удален, но {failed_count} из {deleted_count + failed_count} отношений не удалены"
        
        return True, f"Пользователь {user_id} и все его отношения успешно удалены"
    
    def add_user_to_group(self, user_id: str, group_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Добавляет пользователя в группу."""
        # Проверяем, существует ли пользователь
        users = self._load_users()
        user_exists = False
        
        for user in users:
            if user.get('id') == user_id:
                user_exists = True
                break
        
        # Если пользователь не существует, создаем его
        if not user_exists:
            self.create_user(user_id, f"Пользователь {user_id}")
        
        # Добавляем отношение в Permify
        return self.relationship_model.assign_user_to_group(group_id, user_id, tenant_id)
    
    def remove_user_from_group(self, user_id: str, group_id: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет пользователя из группы."""
        return self.relationship_model.delete_relationship("group", group_id, "member", "user", user_id, tenant_id)
    
    def assign_app_role(self, user_id: str, app_type: str, app_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Назначает пользователю роль в приложении."""
        # Проверяем, существует ли пользователь
        users = self._load_users()
        user_exists = False
        
        for user in users:
            if user.get('id') == user_id:
                user_exists = True
                break
        
        # Если пользователь не существует, создаем его
        if not user_exists:
            self.create_user(user_id, f"Пользователь {user_id}")
        
        # Добавляем отношение в Permify
        return self.relationship_model.assign_user_to_app(app_type, app_id, user_id, role, tenant_id)
    
    def remove_app_role(self, user_id: str, app_type: str, app_id: str, role: str, tenant_id: str = None) -> Tuple[bool, str]:
        """Удаляет роль пользователя в приложении."""
        return self.relationship_model.delete_relationship(app_type, app_id, role, "user", user_id, tenant_id) 