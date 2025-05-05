from .base_controller import BaseController
from app.models import SchemaModel

class SchemaController(BaseController):
    """Контроллер для работы со схемами Permify."""
    
    def __init__(self):
        super().__init__()
        self.schema_model = SchemaModel()
    
    def get_schema_list(self, tenant_id=None):
        """Получает список всех схем."""
        return self.schema_model.get_schema_list(tenant_id)
    
    def get_current_schema(self, tenant_id=None, schema_version=None):
        """Получает текущую или указанную версию схемы."""
        return self.schema_model.get_current_schema(tenant_id, schema_version)
    
    def create_schema(self, schema_content, tenant_id=None):
        """Создает новую схему."""
        return self.schema_model.create_schema(schema_content, tenant_id)
    
    def validate_schema(self, schema_content):
        """Валидирует схему."""
        return self.schema_model.validate_schema(schema_content)
    
    def extract_entities_info(self, schema):
        """Извлекает информацию о сущностях из схемы."""
        return self.schema_model.extract_entities_info(schema)
        
    def generate_schema_from_ui_data(self, apps_data, groups_data):
        """Генерирует схему на основе данных из UI."""
        return self.schema_model.generate_schema_from_ui_data(apps_data, groups_data)
        
    def get_generated_schema_text(self, tenant_id=None):
        """Возвращает текст генерируемой схемы для предпросмотра."""
        success, schema_text = self.schema_model.get_generated_schema_text(tenant_id)
        if success:
            return schema_text
        else:
            raise Exception(f"Ошибка при генерации схемы: {schema_text}") 