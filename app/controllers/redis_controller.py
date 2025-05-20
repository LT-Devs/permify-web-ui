import os
import redis
from typing import Optional, List, Tuple, Dict, Any

class RedisController:
    """Контроллер для управления Redis-кэшем."""
    
    def __init__(self):
        """Инициализация соединения с Redis из переменных окружения или стандартных значений."""
        self.redis_host = os.environ.get("REDIS_HOST", "redis-ars")
        self.redis_port = int(os.environ.get("REDIS_PORT", 6379))
        self.redis_db = int(os.environ.get("REDIS_DB", 0))
        self.redis_password = os.environ.get("REDIS_PASSWORD", None)
        
        self.redis_client = self._connect_to_redis()
        
    def _connect_to_redis(self) -> Optional[redis.Redis]:
        """Создает подключение к Redis."""
        try:
            client = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=self.redis_db,
                password=self.redis_password,
                decode_responses=True,
                socket_timeout=2.0
            )
            # Проверка соединения
            client.ping()
            return client
        except Exception as e:
            print(f"Ошибка подключения к Redis: {str(e)}")
            return None
            
    def flush_cache(self) -> Tuple[bool, str]:
        """Очищает весь кэш Redis."""
        try:
            if self.redis_client:
                self.redis_client.flushdb()
                return True, "Кэш успешно очищен"
            else:
                return False, "Нет подключения к Redis"
        except Exception as e:
            return False, f"Ошибка при очистке кэша: {str(e)}"
    
    def flush_user_permissions(self, user_id: str) -> Tuple[bool, str]:
        """Очищает кэш для конкретного пользователя."""
        try:
            if not self.redis_client:
                return False, "Нет подключения к Redis"
            
            # Создаем шаблон ключа для пользователя и удаляем ключи по шаблону
            deleted_count = 0
            for key in self.redis_client.scan_iter(f"{user_id}:*"):
                self.redis_client.delete(key)
                deleted_count += 1
            
            if deleted_count > 0:
                return True, f"Удалено {deleted_count} ключей для пользователя {user_id}"
            else:
                return True, f"Ключи для пользователя {user_id} не найдены"
                
        except Exception as e:
            return False, f"Ошибка при очистке кэша пользователя: {str(e)}"
    
    def flush_entity_permissions(self, entity_type: str, entity_id: str) -> Tuple[bool, str]:
        """Очищает кэш для конкретной сущности."""
        try:
            if not self.redis_client:
                return False, "Нет подключения к Redis"
            
            # Создаем шаблон ключа для сущности и удаляем ключи по шаблону
            # Формат ключа: {user_id}:{action}:{entity_type}:{entity_id}
            deleted_count = 0
            for key in self.redis_client.scan_iter(f"*:*:{entity_type}:{entity_id}"):
                self.redis_client.delete(key)
                deleted_count += 1
            
            if deleted_count > 0:
                return True, f"Удалено {deleted_count} ключей для сущности {entity_type}:{entity_id}"
            else:
                return True, f"Ключи для сущности {entity_type}:{entity_id} не найдены"
                
        except Exception as e:
            return False, f"Ошибка при очистке кэша сущности: {str(e)}"
    
    def get_cache_stats(self) -> Tuple[bool, Dict[str, Any]]:
        """Получает статистику кэша Redis."""
        try:
            if not self.redis_client:
                return False, {"error": "Нет подключения к Redis"}
            
            # Получаем информацию о кэше через info
            info = self.redis_client.info()
            
            # Подсчитываем ключи
            total_keys = 0
            permission_keys = 0
            
            # Используем scan_iter для избежания блокировки при большом количестве ключей
            for key in self.redis_client.scan_iter("*"):
                total_keys += 1
                if ":" in key and len(key.split(":")) >= 3:  # Проверка формата ключа разрешений
                    permission_keys += 1
            
            stats = {
                "total_keys": total_keys,
                "permission_keys": permission_keys,
                "memory_used": info.get("used_memory_human", "Н/Д"),
                "uptime_days": info.get("uptime_in_days", 0),
                "clients_connected": info.get("connected_clients", 0)
            }
            
            return True, stats
            
        except Exception as e:
            return False, {"error": f"Ошибка при получении статистики: {str(e)}"}
    
    def is_connected(self) -> bool:
        """Проверяет, установлено ли соединение с Redis."""
        if not self.redis_client:
            return False
        
        try:
            # Проверяем соединение простым ping
            return bool(self.redis_client.ping())
        except:
            return False 