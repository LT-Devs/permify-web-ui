import streamlit as st
import json
from .base_view import BaseView
from app.controllers import SchemaController, AppController, BaseController

class IntegrationView(BaseView):
    """Представление для страницы интеграции с примерами кода."""
    
    def __init__(self):
        super().__init__()
        self.schema_controller = SchemaController()
        self.app_controller = AppController()
        self.base_controller = BaseController()
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс интеграции с примерами кода для разных языков."""
        self.show_header("Интеграция с Permify", 
                         "Примеры кода для интеграции с Permify API через различные языки и фреймворки")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("integration_view")
        
        # Получаем данные
        apps = self.app_controller.get_apps(tenant_id)
        success, schema_result = self.schema_controller.get_current_schema(tenant_id)
        
        # Фильтруем только экземпляры приложений (не шаблоны)
        app_instances = [app for app in apps if not app.get('is_template', False) and app.get('id')]
        
        # Вкладки для разных разделов
        tabs = st.tabs(["Экспорт схемы", "Проверка доступа (Check API)", "Go (Gin)", "Python (FastAPI)", "REST API"])
        
        # Вкладка экспорта схемы
        with tabs[0]:
            st.subheader("Экспорт схемы в формате .perm")
            
            if success and schema_result:
                schema_string = schema_result.get("schema_string", "")
                if schema_string:
                    st.code(schema_string, language="bash")
                    
                    # Кнопка для скачивания схемы
                    st.download_button(
                        label="💾 Скачать схему как .perm файл",
                        data=schema_string,
                        file_name="permify_schema.perm",
                        mime="text/plain",
                        key="download_schema"
                    )
                else:
                    st.warning("Схема не определена")
                    
                    # Предложение создать схему
                    st.info("Схема не найдена. Хотите создать новую схему на основе существующих данных?")
                    if st.button("Создать схему", key="create_schema_btn"):
                        with st.spinner("Создание схемы..."):
                            success, result = self.schema_controller.generate_and_apply_schema(tenant_id)
                            if success:
                                st.success("Схема успешно создана!")
                                st.experimental_rerun()
                            else:
                                st.error(f"Ошибка при создании схемы: {result}")
            else:
                st.error("Не удалось загрузить схему")
                
                # Предложение создать схему
                st.info("Схема не найдена. Хотите создать новую схему на основе существующих данных?")
                if st.button("Создать схему", key="create_schema_btn"):
                    with st.spinner("Создание схемы..."):
                        success, result = self.schema_controller.generate_and_apply_schema(tenant_id)
                        if success:
                            st.success("Схема успешно создана!")
                            st.experimental_rerun()
                        else:
                            st.error(f"Ошибка при создании схемы: {result}")
        
        # Вкладка проверки доступа (Check API)
        with tabs[1]:
            st.subheader("Проверка доступа пользователя (Permission Check API)")
            
            # Инструкция по использованию API проверки доступа
            st.markdown("""
            ### Обзор API проверки доступа
            
            Permify позволяет выполнять проверку прав доступа пользователей к ресурсам через API. 
            Основной эндпоинт для проверки: `/v1/tenants/{tenant_id}/permissions/check`
            
            Существует два типа проверок доступа:
            1. **Проверка доступа к ресурсу** - _"Может ли пользователь X выполнить действие Y с ресурсом Z?"_
            2. **Фильтрация ресурсов** - _"К каким ресурсам пользователь X имеет доступ для выполнения действия Y?"_
            """)
            
            # Выбор приложения для примера
            if app_instances:
                selected_app_index = st.selectbox(
                    "Выберите приложение для примера",
                    range(len(app_instances)),
                    format_func=lambda i: f"{app_instances[i].get('display_name')} (ID: {app_instances[i].get('id')})",
                    key="check_app_select"
                )
                
                selected_app = app_instances[selected_app_index]
                app_type = selected_app.get("name")
                app_id = selected_app.get("id")
                
                # Интерактивный тест проверки доступа
                st.markdown("### Интерактивная проверка доступа")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    user_id = st.text_input("ID пользователя", value="1", key="check_user_id")
                    
                with col2:
                    permission = st.selectbox(
                        "Действие (permission)",
                        ["view", "edit", "delete", "create"],
                        key="check_permission"
                    )
                
                if st.button("Проверить доступ", key="check_access_btn"):
                    with st.spinner("Проверка доступа..."):
                        # Формируем запрос для проверки доступа
                        endpoint = f"/v1/tenants/{tenant_id}/permissions/check"
                        check_data = {
                            "entity": {
                                "type": app_type,
                                "id": app_id
                            },
                            "permission": permission,
                            "subject": {
                                "type": "user",
                                "id": user_id
                            }
                        }
                        
                        # Отправляем запрос
                        success, result = self.base_controller.make_api_request(endpoint, check_data)
                        
                        if success:
                            can_access = result.get("can") == "RESULT_ALLOWED"
                            
                            if can_access:
                                st.success(f"✅ Пользователь {user_id} имеет право '{permission}' для {app_type} (ID: {app_id})")
                            else:
                                st.error(f"❌ Пользователь {user_id} НЕ имеет права '{permission}' для {app_type} (ID: {app_id})")
                                
                            # Отображаем дополнительную информацию
                            st.json(result)
                        else:
                            st.error(f"Ошибка при проверке доступа: {result}")
                
                # Пример запроса и ответа
                st.markdown("### Пример запроса и ответа")
                
                check_example_req = f"""{{
  "tenant_id": "{tenant_id}",
  "entity": {{
    "type": "{app_type}",
    "id": "{app_id}"
  }},
  "permission": "view",
  "subject": {{
    "type": "user",
    "id": "1"
  }}
}}"""
                
                check_example_res = """{
  "can": "RESULT_ALLOWED",  // или "RESULT_DENIED"
  "metadata": {
    "check_count": 3
  }
}"""
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Пример запроса:**")
                    st.code(check_example_req, language="json")
                    
                with col2:
                    st.markdown("**Пример ответа:**")
                    st.code(check_example_res, language="json")
                
                # Документация по API
                st.markdown("### Документация по API проверки доступа")
                
                st.markdown("""
                #### Формат запроса
                
                ```json
                {
                  "tenant_id": "t1",
                  "metadata": {
                    "snap_token": "",
                    "schema_version": "",
                    "depth": 20
                  },
                  "entity": {
                    "type": "repository",
                    "id": "1"
                  },
                  "permission": "edit",
                  "subject": {
                    "type": "user",
                    "id": "1"
                  }
                }
                ```
                
                #### Параметры запроса
                
                - `tenant_id` - ID тенанта в Permify
                - `entity.type` - Тип сущности (например, "document", "project", "repository")
                - `entity.id` - ID сущности для проверки доступа
                - `permission` - Действие для проверки (например, "view", "edit", "delete")
                - `subject.type` - Тип субъекта (обычно "user" или "group")
                - `subject.id` - ID субъекта (например, ID пользователя)
                
                #### Формат ответа
                
                ```json
                {
                  "can": "RESULT_ALLOWED",  // или "RESULT_DENIED"
                  "metadata": {
                    "check_count": 3
                  }
                }
                ```
                
                Значение `can` может быть:
                - `RESULT_ALLOWED` - доступ разрешен
                - `RESULT_DENIED` - доступ запрещен
                """)
            else:
                st.warning("Нет доступных приложений для генерации примеров")
        
        # Вкладка с примерами для Go (Gin)
        with tabs[2]:
            st.subheader("Интеграция с Go (Gin)")
            
            # Выбор приложения для примера
            if app_instances:
                selected_app_index = st.selectbox(
                    "Выберите приложение для примера",
                    range(len(app_instances)),
                    format_func=lambda i: f"{app_instances[i].get('display_name')} (ID: {app_instances[i].get('id')})",
                    key="go_app_select"
                )
                
                selected_app = app_instances[selected_app_index]
                app_type = selected_app.get("name")
                app_id = selected_app.get("id")
                
                # Код для установки библиотеки
                st.markdown("#### Установка Permify Go клиента")
                install_code = """go get buf.build/gen/go/permifyco/permify/protocolbuffers/go/base/v1
go get github.com/Permify/permify-go"""
                st.code(install_code, language="bash")
                
                # Код для инициализации клиента
                st.markdown("#### Инициализация клиента")
                init_code = """package main

import (
	"context"
	"log"
	
	permify_payload "buf.build/gen/go/permifyco/permify/protocolbuffers/go/base/v1"
	permify_grpc "github.com/Permify/permify-go/grpc"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

func main() {
	// Инициализация клиента Permify
	client, err := permify_grpc.NewClient(
		permify_grpc.Config{
			Endpoint: "localhost:3478", // Обновите на ваш endpoint
		},
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	if err != nil {
		log.Fatalf("Ошибка при создании клиента: %v", err)
	}
	defer client.Close()
	
	// Дальнейший код...
}"""
                st.code(init_code, language="go")
                
                # Код для проверки разрешений
                st.markdown("#### Проверка разрешений (в Gin)")
                check_code = f"""package middlewares

import (
	"net/http"
	
	"github.com/gin-gonic/gin"
	permify_payload "buf.build/gen/go/permifyco/permify/protocolbuffers/go/base/v1"
	permify_grpc "github.com/Permify/permify-go/grpc"
)

// PermifyClient - глобальный клиент Permify
var PermifyClient *permify_grpc.Client

// PermifyAuth - middleware для проверки разрешений
func PermifyAuth(action string) gin.HandlerFunc {{
	return func(c *gin.Context) {{
		// Получаем ID пользователя и объекта
		userID := c.GetString("userID") // ID должен быть получен из вашей системы аутентификации
		objectID := c.Param("id")       // Предполагаем, что ID объекта передается в URL
		
		// Проверяем разрешения через Permify
		cr, err := PermifyClient.Permission.Check(c.Request.Context(), &permify_payload.PermissionCheckRequest{{
			TenantId: "{tenant_id}",
			Entity: &permify_payload.Entity{{
				Type: "{app_type}",
				Id:   objectID,
			}},
			Permission: action,
			Subject: &permify_payload.Subject{{
				Type: "user",
				Id:   userID,
			}},
		}})
		
		if err != nil {{
			c.JSON(http.StatusInternalServerError, gin.H{{"error": "Ошибка проверки разрешений"}})
			c.Abort()
			return
		}}
		
		if cr.GetCan() != permify_payload.PermissionCheckResponse_RESULT_ALLOWED {{
			c.JSON(http.StatusForbidden, gin.H{{"error": "Доступ запрещен"}})
			c.Abort()
			return
		}}
		
		c.Next()
	}}
}}

// Пример использования в маршрутах:
/*
func SetupRoutes(r *gin.Engine) {{
	api := r.Group("/api")
	
	// Защищенные маршруты
	{app_type} := api.Group("/{app_type}")
	{{
		{app_type}.GET("/:id", PermifyAuth("view"), Get{app_type}ByID)
		{app_type}.PUT("/:id", PermifyAuth("edit"), Update{app_type})
		{app_type}.DELETE("/:id", PermifyAuth("delete"), Delete{app_type})
	}}
}}
*/
"""
                st.code(check_code, language="go")
                
                # Пример всего приложения
                st.markdown("#### Полный пример приложения")
                full_example = f"""package main

import (
	"log"
	
	"github.com/gin-gonic/gin"
	permify_payload "buf.build/gen/go/permifyco/permify/protocolbuffers/go/base/v1"
	permify_grpc "github.com/Permify/permify-go/grpc"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

var permifyClient *permify_grpc.Client

func init() {{
	// Инициализация клиента Permify
	var err error
	permifyClient, err = permify_grpc.NewClient(
		permify_grpc.Config{{
			Endpoint: "localhost:3478", // Обновите на ваш endpoint
		}},
		grpc.WithTransportCredentials(insecure.NewCredentials()),
	)
	
	if err != nil {{
		log.Fatalf("Ошибка при создании клиента Permify: %v", err)
	}}
}}

// PermifyAuth middleware для проверки разрешений
func PermifyAuth(action string) gin.HandlerFunc {{
	return func(c *gin.Context) {{
		userID := c.GetString("userID") // ID должен быть получен из вашей системы аутентификации
		objectID := c.Param("id")
		
		cr, err := permifyClient.Permission.Check(c.Request.Context(), &permify_payload.PermissionCheckRequest{{
			TenantId: "{tenant_id}",
			Entity: &permify_payload.Entity{{
				Type: "{app_type}",
				Id:   objectID,
			}},
			Permission: action,
			Subject: &permify_payload.Subject{{
				Type: "user",
				Id:   userID,
			}},
		}})
		
		if err != nil {{
			c.AbortWithStatusJSON(500, gin.H{{"error": "Ошибка проверки разрешений"}})
			return
		}}
		
		if cr.GetCan() != permify_payload.PermissionCheckResponse_RESULT_ALLOWED {{
			c.AbortWithStatusJSON(403, gin.H{{"error": "Доступ запрещен"}})
			return
		}}
		
		c.Next()
	}}
}}

// Хендлер для эмуляции получения ID пользователя
func AuthMiddleware() gin.HandlerFunc {{
	return func(c *gin.Context) {{
		// В реальном приложении, здесь будет проверка JWT или куки сессии
		c.Set("userID", "1") // Для демонстрации используем ID пользователя "1"
		c.Next()
	}}
}}

func main() {{
	r := gin.Default()
	
	// Применяем middleware для авторизации
	r.Use(AuthMiddleware())
	
	api := r.Group("/api")
	
	// API для работы с {app_type}
	{app_type}API := api.Group("/{app_type}")
	{{
		{app_type}API.GET("/:id", PermifyAuth("view"), func(c *gin.Context) {{
			id := c.Param("id")
			c.JSON(200, gin.H{{
				"id": id,
				"type": "{app_type}",
				"message": "Объект успешно просмотрен",
			}})
		}})
		
		{app_type}API.PUT("/:id", PermifyAuth("edit"), func(c *gin.Context) {{
			id := c.Param("id")
			c.JSON(200, gin.H{{
				"id": id,
				"type": "{app_type}",
				"message": "Объект успешно обновлен",
			}})
		}})
		
		{app_type}API.DELETE("/:id", PermifyAuth("delete"), func(c *gin.Context) {{
			id := c.Param("id")
			c.JSON(200, gin.H{{
				"id": id,
				"type": "{app_type}",
				"message": "Объект успешно удален",
			}})
		}})
	}}
	
	log.Println("Сервер запущен на :8080")
	r.Run(":8080")
}}
"""
                st.code(full_example, language="go")
            else:
                st.warning("Нет доступных приложений для генерации примеров")
        
        # Вкладка с примерами для Python (FastAPI)
        with tabs[3]:
            st.subheader("Интеграция с Python (FastAPI)")
            
            # Выбор приложения для примера
            if app_instances:
                selected_app_index = st.selectbox(
                    "Выберите приложение для примера",
                    range(len(app_instances)),
                    format_func=lambda i: f"{app_instances[i].get('display_name')} (ID: {app_instances[i].get('id')})",
                    key="python_app_select"
                )
                
                selected_app = app_instances[selected_app_index]
                app_type = selected_app.get("name")
                app_id = selected_app.get("id")
                
                # Код для установки библиотеки
                st.markdown("#### Установка Permify Python клиента")
                install_code = """pip install permify-python"""
                st.code(install_code, language="bash")
                
                # Код для инициализации клиента
                st.markdown("#### Инициализация клиента")
                init_code = """from permify.client import PermifyClient

# Инициализация клиента
permify_client = PermifyClient(host="localhost:3478")
"""
                st.code(init_code, language="python")
                
                # Код для проверки разрешений
                st.markdown("#### Проверка разрешений (в FastAPI)")
                check_code = f"""from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, Optional
from permify.client import PermifyClient
from pydantic import BaseModel

app = FastAPI()

# Инициализация клиента Permify
permify_client = PermifyClient(host="localhost:3478")

# Эмуляция аутентификации (в реальности здесь будет ваша логика JWT)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Функция для получения текущего пользователя
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    # В реальности здесь будет декодирование JWT
    # Для демонстрации возвращаем пользователя с ID 1
    return {{"id": "1", "username": "example_user"}}

# Middleware для проверки разрешений
def permify_auth(action: str, object_type: str = "{app_type}"):
    async def auth_dependency(user: dict = Depends(get_current_user), object_id: str = None):
        if not object_id:
            return user
            
        try:
            # Проверка разрешения через Permify
            result = permify_client.permission.check(
                tenant_id="{tenant_id}",
                entity={{"type": object_type, "id": object_id}},
                permission=action,
                subject={{"type": "user", "id": user["id"]}}
            )
            
            if not result.get("can"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для выполнения этого действия"
                )
                
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при проверке прав доступа: {{str(e)}}"
            )
    
    return auth_dependency

# Маршруты API
@app.get("/{app_type}/{{object_id}}")
async def get_object(
    object_id: str,
    user: dict = Depends(permify_auth("view"))
):
    return {{"id": object_id, "type": "{app_type}", "message": "Объект успешно просмотрен"}}

@app.put("/{app_type}/{{object_id}}")
async def update_object(
    object_id: str,
    user: dict = Depends(permify_auth("edit"))
):
    return {{"id": object_id, "type": "{app_type}", "message": "Объект успешно обновлен"}}

@app.delete("/{app_type}/{{object_id}}")
async def delete_object(
    object_id: str,
    user: dict = Depends(permify_auth("delete"))
):
    return {{"id": object_id, "type": "{app_type}", "message": "Объект успешно удален"}}
"""
                st.code(check_code, language="python")
                
                # Полный пример с миграциями
                st.markdown("#### Полный пример с настройкой схемы и отношений")
                full_example = f"""from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Annotated, List, Dict, Any
from permify.client import PermifyClient
from pydantic import BaseModel

app = FastAPI(title="Permify FastAPI Demo")

# Инициализация клиента Permify
permify_client = PermifyClient(host="localhost:3478")

# Определение схемы Permify для вашего приложения
PERMIFY_SCHEMA = '''
entity user {{}}

entity {app_type} {{
    relation owner @user
    relation editor @user
    relation viewer @user
    
    action view = owner or editor or viewer
    action edit = owner or editor
    action delete = owner
}}
'''

# Модели данных
class User(BaseModel):
    id: str
    username: str

class {app_type.capitalize()}Create(BaseModel):
    title: str
    content: str
    owner_id: str

class {app_type.capitalize()}Response(BaseModel):
    id: str
    title: str
    content: str
    owner_id: str

# Эмуляция аутентификации
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Функция для получения текущего пользователя
async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> User:
    # В реальности здесь будет декодирование JWT
    return User(id="1", username="example_user")

# Middleware для проверки разрешений
def permify_auth(action: str, object_type: str = "{app_type}"):
    async def auth_dependency(
        object_id: str, 
        user: User = Depends(get_current_user)
    ):
        try:
            # Проверка разрешения через Permify
            result = permify_client.permission.check(
                tenant_id="{tenant_id}",
                entity={{"type": object_type, "id": object_id}},
                permission=action,
                subject={{"type": "user", "id": user.id}}
            )
            
            if not result.get("can"):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Недостаточно прав для выполнения этого действия"
                )
                
            return user
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Ошибка при проверке прав доступа: {{str(e)}}"
            )
    
    return auth_dependency

# События приложения
@app.on_event("startup")
async def startup_event():
    # Создание или обновление схемы Permify
    try:
        schema_result = permify_client.schema.write(
            tenant_id="{tenant_id}",
            schema=PERMIFY_SCHEMA
        )
        print(f"Schema created with version: {{schema_result.get('schema_version')}}")
    except Exception as e:
        print(f"Error creating schema: {{e}}")

# Фейковое хранилище данных
{app_type}_db: Dict[str, {app_type.capitalize()}Response] = {{}}

# Маршруты API
@app.post("/{app_type}/", response_model={app_type.capitalize()}Response)
async def create_{app_type}(
    item: {app_type.capitalize()}Create,
    user: User = Depends(get_current_user)
):
    # Создаем новый объект
    new_id = str(len({app_type}_db) + 1)
    new_{app_type} = {app_type.capitalize()}Response(
        id=new_id,
        title=item.title,
        content=item.content,
        owner_id=item.owner_id
    )
    {app_type}_db[new_id] = new_{app_type}
    
    # Создаем отношение в Permify
    try:
        permify_client.data.write_relationships(
            tenant_id="{tenant_id}",
            tuples=[
                {{
                    "entity": {{"type": "{app_type}", "id": new_id}},
                    "relation": "owner",
                    "subject": {{"type": "user", "id": item.owner_id}}
                }}
            ]
        )
    except Exception as e:
        print(f"Error creating relationship: {{e}}")
    
    return new_{app_type}

@app.get("/{app_type}/{{object_id}}", response_model={app_type.capitalize()}Response)
async def get_{app_type}(
    object_id: str,
    _: User = Depends(permify_auth("view"))
):
    if object_id not in {app_type}_db:
        raise HTTPException(status_code=404, detail="{app_type.capitalize()} not found")
    return {app_type}_db[object_id]

@app.put("/{app_type}/{{object_id}}", response_model={app_type.capitalize()}Response)
async def update_{app_type}(
    object_id: str,
    item: {app_type.capitalize()}Create,
    _: User = Depends(permify_auth("edit"))
):
    if object_id not in {app_type}_db:
        raise HTTPException(status_code=404, detail="{app_type.capitalize()} not found")
    
    updated_{app_type} = {app_type.capitalize()}Response(
        id=object_id,
        title=item.title,
        content=item.content,
        owner_id=item.owner_id
    )
    {app_type}_db[object_id] = updated_{app_type}
    return updated_{app_type}

@app.delete("/{app_type}/{{object_id}}")
async def delete_{app_type}(
    object_id: str,
    _: User = Depends(permify_auth("delete"))
):
    if object_id not in {app_type}_db:
        raise HTTPException(status_code=404, detail="{app_type.capitalize()} not found")
    
    del {app_type}_db[object_id]
    return {{"message": "{app_type.capitalize()} successfully deleted"}}

@app.post("/{app_type}/{{object_id}}/share")
async def share_{app_type}(
    object_id: str,
    user_id: str,
    role: str,
    current_user: User = Depends(get_current_user)
):
    if object_id not in {app_type}_db:
        raise HTTPException(status_code=404, detail="{app_type.capitalize()} not found")
    
    # Проверяем, что текущий пользователь имеет права на редактирование
    try:
        result = permify_client.permission.check(
            tenant_id="{tenant_id}",
            entity={{"type": "{app_type}", "id": object_id}},
            permission="edit",
            subject={{"type": "user", "id": current_user.id}}
        )
        
        if not result.get("can"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="У вас нет прав для предоставления доступа"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при проверке прав доступа: {{str(e)}}"
        )
    
    # Устанавливаем новое отношение в зависимости от роли
    try:
        relation = "viewer"  # По умолчанию
        if role == "editor":
            relation = "editor"
        elif role == "owner":
            relation = "owner"
        
        permify_client.data.write_relationships(
            tenant_id="{tenant_id}",
            tuples=[
                {{
                    "entity": {{"type": "{app_type}", "id": object_id}},
                    "relation": relation,
                    "subject": {{"type": "user", "id": user_id}}
                }}
            ]
        )
        
        return {{"message": f"Доступ {{role}} предоставлен пользователю {{user_id}}"}}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка при установке отношения: {{str(e)}}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
"""
                st.code(full_example, language="python")
            else:
                st.warning("Нет доступных приложений для генерации примеров")
        
        # Вкладка с примерами для REST API
        with tabs[4]:
            st.subheader("Использование REST API")
            
            # Выбор приложения для примера
            if app_instances:
                selected_app_index = st.selectbox(
                    "Выберите приложение для примера",
                    range(len(app_instances)),
                    format_func=lambda i: f"{app_instances[i].get('display_name')} (ID: {app_instances[i].get('id')})",
                    key="rest_app_select"
                )
                
                selected_app = app_instances[selected_app_index]
                app_type = selected_app.get("name")
                app_id = selected_app.get("id")
                
                # Пример создания схемы
                st.markdown("#### Создание или обновление схемы")
                schema_api_code = f"""curl -X POST http://localhost:9010/schema/write \\
    -H "Content-Type: application/json" \\
    -d '{{"tenant_id": "{tenant_id}", "schema": "entity user {{}}\nentity {app_type} {{\n  relation owner @user\n  relation editor @user\n  relation viewer @user\n  \n  action view = owner or editor or viewer\n  action edit = owner or editor\n  action delete = owner\n}}"}}' 
"""
                st.code(schema_api_code, language="bash")
                
                # Пример создания отношений
                st.markdown("#### Создание отношений")
                relation_api_code = f"""curl -X POST http://localhost:9010/data/write/relationships \\
    -H "Content-Type: application/json" \\
    -d '{{"tenant_id": "{tenant_id}", "tuples": [{{"entity": {{"type": "{app_type}", "id": "{app_id}"}}, "relation": "owner", "subject": {{"type": "user", "id": "1"}}}}]}}' 
"""
                st.code(relation_api_code, language="bash")
                
                # Пример проверки доступа
                st.markdown("#### Проверка доступа")
                check_api_code = f"""curl -X POST http://localhost:9010/permission/check \\
    -H "Content-Type: application/json" \\
    -d '{{"tenant_id": "{tenant_id}", "entity": {{"type": "{app_type}", "id": "{app_id}"}}, "permission": "view", "subject": {{"type": "user", "id": "1"}}}}' 
"""
                st.code(check_api_code, language="bash")
                
                # Пример получения отношений
                st.markdown("#### Получение отношений")
                read_api_code = f"""curl -X POST http://localhost:9010/data/read/relationships \\
    -H "Content-Type: application/json" \\
    -d '{{"tenant_id": "{tenant_id}", "entity": {{"type": "{app_type}", "id": "{app_id}"}}}}' 
"""
                st.code(read_api_code, language="bash")
                
                # Пример фильтрации объектов
                st.markdown("#### Фильтрация объектов (lookup entity)")
                lookup_api_code = f"""curl -X POST http://localhost:9010/permission/lookup_entity \\
    -H "Content-Type: application/json" \\
    -d '{{"tenant_id": "{tenant_id}", "entity_type": "{app_type}", "permission": "view", "subject": {{"type": "user", "id": "1"}}}}' 
"""
                st.code(lookup_api_code, language="bash")
                
                # Пример удаления отношений
                st.markdown("#### Удаление отношений")
                delete_api_code = f"""curl -X POST http://localhost:9010/data/delete \\
    -H "Content-Type: application/json" \\
    -d '{{"tenant_id": "{tenant_id}", "tuples": [{{"entity": {{"type": "{app_type}", "id": "{app_id}"}}, "relation": "viewer", "subject": {{"type": "user", "id": "1"}}}}]}}' 
"""
                st.code(delete_api_code, language="bash")
                
                # Полный пример последовательности API-вызовов
                st.markdown("#### Полный пример последовательности API-вызовов")
                full_api_code = """#!/bin/bash
# Пример скрипта для демонстрации работы с Permify REST API

# Настройки
PERMIFY_URL="http://localhost:9010"
TENANT_ID="t1"

echo "1. Создание схемы..."
curl -X POST "${PERMIFY_URL}/schema/write" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\": \"${TENANT_ID}\", \"schema\": \"entity user {}\\nentity document {\\n  relation owner @user\\n  relation editor @user\\n  relation viewer @user\\n  \\n  action view = owner or editor or viewer\\n  action edit = owner or editor\\n  action delete = owner\\n}\"}" | jq

# Сохраняем версию схемы для дальнейшего использования
SCHEMA_VERSION=$(curl -s -X POST "${PERMIFY_URL}/schema/read" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\": \"${TENANT_ID}\"}" | jq -r '.schema_version')

echo "Текущая версия схемы: ${SCHEMA_VERSION}"

echo "2. Создание отношений..."
curl -X POST "${PERMIFY_URL}/data/write/relationships" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\": \"${TENANT_ID}\", \"metadata\": {\"schema_version\": \"${SCHEMA_VERSION}\"}, \"tuples\": [{\"entity\": {\"type\": \"document\", \"id\": \"1\"}, \"relation\": \"owner\", \"subject\": {\"type\": \"user\", \"id\": \"1\"}}]}" | jq

# Сохраняем снапшот для дальнейшего использования
SNAP_TOKEN=$(curl -s -X POST "${PERMIFY_URL}/data/read/relationships" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\": \"${TENANT_ID}\"}" | jq -r '.snap_token')

echo "Текущий снапшот: ${SNAP_TOKEN}"

echo "3. Проверка доступа..."
curl -X POST "${PERMIFY_URL}/permission/check" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\": \"${TENANT_ID}\", \"metadata\": {\"snap_token\": \"${SNAP_TOKEN}\", \"schema_version\": \"${SCHEMA_VERSION}\"}, \"entity\": {\"type\": \"document\", \"id\": \"1\"}, \"permission\": \"view\", \"subject\": {\"type\": \"user\", \"id\": \"1\"}}" | jq

echo "4. Фильтрация объектов..."
curl -X POST "${PERMIFY_URL}/permission/lookup_entity" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\": \"${TENANT_ID}\", \"metadata\": {\"snap_token\": \"${SNAP_TOKEN}\", \"schema_version\": \"${SCHEMA_VERSION}\"}, \"entity_type\": \"document\", \"permission\": \"view\", \"subject\": {\"type\": \"user\", \"id\": \"1\"}}" | jq

echo "5. Добавление нового отношения..."
curl -X POST "${PERMIFY_URL}/data/write/relationships" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\": \"${TENANT_ID}\", \"metadata\": {\"schema_version\": \"${SCHEMA_VERSION}\"}, \"tuples\": [{\"entity\": {\"type\": \"document\", \"id\": \"2\"}, \"relation\": \"viewer\", \"subject\": {\"type\": \"user\", \"id\": \"1\"}}]}" | jq

echo "6. Повторная фильтрация объектов после добавления..."
curl -X POST "${PERMIFY_URL}/permission/lookup_entity" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\": \"${TENANT_ID}\", \"entity_type\": \"document\", \"permission\": \"view\", \"subject\": {\"type\": \"user\", \"id\": \"1\"}}" | jq

echo "7. Удаление отношения..."
curl -X POST "${PERMIFY_URL}/data/delete" \
    -H "Content-Type: application/json" \
    -d "{\"tenant_id\": \"${TENANT_ID}\", \"tuples\": [{\"entity\": {\"type\": \"document\", \"id\": \"2\"}, \"relation\": \"viewer\", \"subject\": {\"type\": \"user\", \"id\": \"1\"}}]}" | jq

echo "Готово!"
"""
                st.code(full_api_code, language="bash")
            else:
                st.warning("Нет доступных приложений для генерации примеров") 