import streamlit as st
from .base_view import BaseView
from app.controllers import RedisController

class CacheView(BaseView):
    """Представление для управления кэшем Redis."""
    
    def __init__(self):
        super().__init__()
        self.redis_controller = RedisController()
    
    def render(self, skip_status_check=False):
        """Отображает интерфейс управления кэшем Redis."""
        self.show_header("Управление кэшем", 
                       "Инструменты для работы с Redis-кэшем", 
                       icon="🔄")
        
        if not skip_status_check and not self.show_status():
            return
        
        tenant_id = self.get_tenant_id("cache_view")
        
        # Карточка с информацией о кэше
        st.markdown("""
        <div class="card">
            <div class="card-title">ℹ️ Информация о кэше</div>
            <div class="card-content">
                <p>Система использует Redis для кэширования данных о правах доступа и других объектах. 
                Сброс кэша может потребоваться при изменении прав доступа или обновлении схемы.</p>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Статус подключения
        st.subheader("Статус подключения")
        
        is_connected = self.redis_controller.is_connected()
        
        if is_connected:
            status_html = """
            <div style="background-color: rgba(40, 167, 69, 0.1); border: 1px solid rgba(40, 167, 69, 0.5); color: var(--text); padding: 1rem; border-radius: var(--radius); margin: 1rem 0;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.5rem; margin-right: 0.75rem;">✅</span>
                    <div>
                        <div style="font-weight: 600; font-size: 1.1rem;">Соединение с Redis установлено</div>
                        <div style="margin-top: 0.25rem; font-size: 0.9rem;">
                            Сервер кэширования работает нормально.
                        </div>
                    </div>
                </div>
            </div>
            """
            st.markdown(status_html, unsafe_allow_html=True)
            
            # Получаем статистику кэша
            success, stats = self.redis_controller.get_cache_stats()
            if success:
                st.subheader("Статистика кэша")
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Всего ключей", stats.get("total_keys", 0))
                with col2:
                    st.metric("Ключи разрешений", stats.get("permission_keys", 0))
                with col3:
                    st.metric("Использование памяти", stats.get("memory_used", "Н/Д"))
        else:
            status_html = """
            <div style="background-color: rgba(220, 53, 69, 0.1); border: 1px solid rgba(220, 53, 69, 0.5); color: var(--text); padding: 1rem; border-radius: var(--radius); margin: 1rem 0;">
                <div style="display: flex; align-items: center;">
                    <span style="font-size: 1.5rem; margin-right: 0.75rem;">❌</span>
                    <div>
                        <div style="font-weight: 600; font-size: 1.1rem;">Нет соединения с Redis</div>
                        <div style="margin-top: 0.25rem; font-size: 0.9rem;">
                            Проверьте настройки подключения и доступность сервера Redis.
                        </div>
                    </div>
                </div>
            </div>
            """
            st.markdown(status_html, unsafe_allow_html=True)
        
        # Конфигурация Redis
        st.subheader("Конфигурация Redis")
        
        # Отображаем информацию о настройках подключения к Redis
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(f"**Хост:** `{self.redis_controller.redis_host}`")
            st.markdown(f"**Порт:** `{self.redis_controller.redis_port}`")
        
        with col2:
            st.markdown(f"**База данных:** `{self.redis_controller.redis_db}`")
            password_display = "Установлен" if self.redis_controller.redis_password else "Не установлен"
            st.markdown(f"**Пароль:** `{password_display}`")
        
        # Управление кэшем
        st.subheader("Управление кэшем")
        
        # Добавляем объяснение и кнопку сброса кэша
        cache_col1, cache_col2 = st.columns([3, 1])
        
        with cache_col1:
            st.markdown("""
            Сброс кэша удалит все кэшированные данные из Redis. Это может потребоваться для:
            - Обновления данных о правах доступа
            - Применения изменений в схеме доступа
            - Устранения проблем с устаревшими данными
            
            После сброса кэша, данные будут автоматически восстановлены при следующих запросах.
            """)
        
        with cache_col2:
            st.write("")
            st.write("")
            if st.button("🗑️ Сбросить весь кэш", key="flush_all_redis_cache", type="primary"):
                success, message = self.redis_controller.flush_cache()
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
        
        # Расширенная информация
        with st.expander("Подробные сведения о Redis"):
            st.markdown("""
            ### О Redis
            
            Redis (Remote Dictionary Server) - это быстрое хранилище данных в памяти, используемое в качестве базы данных, кэша, брокера сообщений и очереди.
            
            ### Использование в системе
            
            В данной системе Redis используется для:
            - Кэширования прав доступа для увеличения скорости проверки
            - Хранения временного состояния приложения
            - Хранения сессий пользователей
            
            ### Формат кэширования прав доступа
            
            Ключи прав доступа в Redis имеют следующий формат:
            ```
            {user_id}:{action}:{entity_type}:{entity_id}
            ```
            
            Например:
            ```
            user123:view:report:456
            ```
            
            ### Переменные окружения
            
            Для настройки подключения к Redis используются следующие переменные окружения:
            - `REDIS_HOST`: адрес сервера Redis
            - `REDIS_PORT`: порт сервера Redis
            - `REDIS_DB`: номер базы данных Redis
            - `REDIS_PASSWORD`: пароль для подключения к Redis
            
            По умолчанию используется адрес `redis-ars` и порт `6379`.
            """) 