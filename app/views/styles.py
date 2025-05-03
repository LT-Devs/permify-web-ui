"""Модуль для хранения общих стилей CSS для приложения."""

# Стили для темного режима
DARK_MODE_STYLES = """
<style>
/* Улучшаем контрастность текста и фона для темного режима */
input[type="text"] {
    color: #e0e0e0 !important; 
    background-color: #2d3035 !important;
    border: 1px solid #4e5259 !important;
}

.dataframe {
    background-color: #2d3035 !important;
    color: #e0e0e0 !important;
}

.dataframe th {
    background-color: #1e2025 !important;
    color: #e0e0e0 !important;
    font-weight: bold !important;
}

.dataframe td {
    background-color: #2d3035 !important;
    color: #e0e0e0 !important;
}

/* Улучшаем видимость в темном режиме */
.stSelectbox label, .stTextInput label, .stCheckbox label {
    color: #e0e0e0 !important;
    font-weight: bold !important;
}

.stSelectbox > div > div {
    background-color: #2d3035 !important;
    color: #e0e0e0 !important;
    border: 1px solid #4e5259 !important;
}

/* Улучшаем внешний вид чекбоксов */
.stCheckbox {
    background-color: #2d3035;
    padding: 6px 10px;
    border-radius: 5px;
    margin-bottom: 4px;
}

/* Улучшаем видимость меток чекбоксов */
.stCheckbox label span {
    color: #e0e0e0 !important;
    font-weight: normal !important;
}

/* Улучшаем контрастность кнопок в темном режиме */
.stButton button {
    background-color: #3d4045 !important;
    color: #e0e0e0 !important;
    border: 1px solid #4e5259 !important;
}

/* Стиль для основных кнопок */
.stButton button[kind="primary"] {
    background-color: #4257b2 !important;
    color: #ffffff !important;
    border: none !important;
}

/* Стиль для информационных сообщений */
.stAlert {
    background-color: #2d3035 !important;
    color: #e0e0e0 !important;
    border: 1px solid #4e5259 !important;
}

/* Стиль для заголовков */
.stMarkdown h3, .stMarkdown h4 {
    color: #e0e0e0 !important;
}

/* Стиль для контейнеров */
.stExpander {
    background-color: #1e2025 !important;
    border: 1px solid #4e5259 !important;
}

/* Стиль для контейнеров элементов */
.element-container {
    margin-bottom: 1rem;
}

/* Стили для формы создания объекта */
.actions-container {
    background-color: #1e2025;
    padding: 15px;
    border-radius: 5px;
    margin-top: 10px;
    margin-bottom: 15px;
    border: 1px solid #4e5259;
}

/* Стиль для действий в форме */
.action-row {
    background-color: #2d3035;
    border-radius: 5px;
    padding: 8px;
    margin-bottom: 8px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.3);
    border: 1px solid #4e5259;
}

/* Стиль для заголовка таблицы */
.perm-header {
    background-color: #1e2025;
    padding: 8px 12px;
    border-radius: 5px;
    margin-bottom: 12px;
    font-weight: bold;
    color: #e0e0e0;
}

/* Стиль для контейнеров отношений */
.relation-card {
    background-color: #1e2025;
    padding: 15px;
    border-radius: 5px;
    margin-bottom: 15px;
    border: 1px solid #4e5259;
}

/* Подсветка строк в таблицах при наведении */
.dataframe tbody tr:hover {
    background-color: #3d4045 !important;
}
</style>
"""

# Основная функция для получения стилей
def get_dark_mode_styles():
    """Возвращает CSS-стили для темного режима."""
    return DARK_MODE_STYLES 