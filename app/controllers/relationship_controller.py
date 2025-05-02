from .base_controller import BaseController
from app.models import RelationshipModel

class RelationshipController(BaseController):
    """Контроллер для работы с отношениями (tuples) Permify."""
    
    def __init__(self):
        super().__init__()
        self.relationship_model = RelationshipModel()
    
    def get_relationships(self, tenant_id=None, filters=None):
        """Получает список отношений с возможностью фильтрации."""
        return self.relationship_model.get_relationships(tenant_id, filters)
    
    def create_relationship(self, entity_type, entity_id, relation, subject_type, subject_id, tenant_id=None):
        """Создает новое отношение."""
        return self.relationship_model.create_relationship(
            entity_type, entity_id, relation, subject_type, subject_id, tenant_id
        )
    
    def delete_relationship(self, entity_type, entity_id, relation, subject_type, subject_id, tenant_id=None):
        """Удаляет отношение."""
        return self.relationship_model.delete_relationship(
            entity_type, entity_id, relation, subject_type, subject_id, tenant_id
        )
    
    def check_permission(self, entity_type, entity_id, permission, user_id, tenant_id=None, schema_version=None):
        """Проверяет разрешение."""
        return self.relationship_model.check_permission(
            entity_type, entity_id, permission, user_id, tenant_id, schema_version
        )
    
    def delete_multiple_relationships(self, relationships, tenant_id=None):
        """Удаляет несколько отношений."""
        return self.relationship_model.delete_multiple_relationships(relationships, tenant_id) 