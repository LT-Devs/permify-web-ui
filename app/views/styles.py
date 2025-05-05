"""Модуль для хранения общих стилей CSS для приложения."""

# Стили для современного Streamlit-приложения
MODERN_STYLES = """
<style>
/* Основные переменные */
:root {
    --primary: #4A90E2;
    --primary-light: #6ba5e8;
    --primary-dark: #3a72b4;
    --success: #28a745;
    --info: #17a2b8;
    --warning: #ffc107;
    --danger: #dc3545;
    --light: #f8f9fa;
    --dark: #1a1c22;
    --secondary-bg: #262930;
    --border: #494c56;
    --text: #F0F2F6;
    --text-secondary: #c2c5d1;
    --radius: 0.5rem;
    --shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    --transition: all 0.2s ease;
}

/* Принудительное расширение всех контейнеров Streamlit */
div[data-testid="stVerticalBlock"] > div:first-child {
    max-width: 100% !important;
    width: 100% !important;
}

/* Глобальное принудительное расширение */
.stApp > header + div > div {
    max-width: 100% !important;
}

div[data-testid="stAppViewContainer"] > div > div > div {
    max-width: 100% !important;
}

/* Увеличение максимальной ширины контейнера */
.block-container {
    max-width: 98% !important;
    padding-left: 1rem !important;
    padding-right: 1rem !important;
}

/* Принудительное увеличение ширины основного контейнера */
.css-18e3th9 {
    padding-left: 1rem !important;
    padding-right: 1rem !important;
    max-width: 98% !important;
}

/* Расширение содержимого на всю доступную ширину */
.css-1y4p8pa {
    width: 100% !important;
    max-width: 98% !important;
}

/* Полная ширина для всех внутренних контейнеров */
.css-1r6slb0, .css-keje6w, .css-1l4w6pd, .css-1offfwp {
    max-width: 98% !important;
    width: 100% !important;
}

/* Дополнительные стили для контейнеров */
.css-ocqkz7, .css-k1vhr4, .css-9s5bis, .css-1544g2n {
    max-width: 98% !important;
    width: 100% !important;
}

/* Принудительное расширение главного контейнера */
.main .block-container {
    max-width: 98% !important;
}

/* Расширение контейнеров таблиц */
.stDataFrame, .css-1jgnl, .css-1xarl3l {
    width: 100% !important;
    max-width: 100% !important;
}

/* Настройка внутренних отступов контейнеров */
.css-1kyxreq {
    padding-left: 0.5rem !important;
    padding-right: 0.5rem !important;
}

/* Улучшение использования пространства в макете */
.main .block-container {
    padding-top: 2rem !important;
    max-width: 98% !important;
}

/* Подстройка ширины сайдбара */
.css-1d391kg {
    width: 14rem !important;
}

/* Стили для полей ввода */
input[type="text"], textarea, .stTextInput > div > div {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    background-color: var(--secondary-bg) !important;
    color: var(--text) !important;
    transition: var(--transition) !important;
}

input[type="text"]:focus, textarea:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 2px rgba(74, 144, 226, 0.25) !important;
}

/* Улучшение выпадающих списков */
.stSelectbox > div > div {
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    background-color: var(--secondary-bg) !important;
    color: var(--text) !important;
}

/* Улучшение аккордеонов и экспандеров */
.stExpander {
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    background-color: var(--secondary-bg) !important;
    margin-bottom: 1rem !important;
    overflow: hidden !important;
}

.stExpander > div:first-child {
    background-color: var(--secondary-bg) !important;
    border-bottom: 1px solid var(--border) !important;
    padding: 0.75rem 1rem !important;
}

/* Улучшение таблиц */
.dataframe {
    border-collapse: separate !important;
    border-spacing: 0 !important;
    border-radius: var(--radius) !important;
    overflow: hidden !important;
    width: 100% !important;
    margin-bottom: 1rem !important;
    border: 1px solid var(--border) !important;
}

.dataframe th {
    background-color: var(--secondary-bg) !important;
    color: var(--text) !important;
    font-weight: 600 !important;
    padding: 0.75rem 1rem !important;
    text-align: left !important;
    border-bottom: 2px solid var(--border) !important;
}

.dataframe td {
    padding: 0.75rem 1rem !important;
    border-bottom: 1px solid var(--border) !important;
    color: var(--text) !important;
    background-color: var(--dark) !important;
}

.dataframe tr:last-child td {
    border-bottom: none !important;
}

.dataframe tbody tr:hover td {
    background-color: rgba(74, 144, 226, 0.1) !important;
}

/* Стили для компонентов-карточек */
.card {
    background-color: var(--secondary-bg) !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    padding: 1.25rem !important;
    margin-bottom: 1rem !important;
    box-shadow: var(--shadow) !important;
    transition: var(--transition) !important;
}

.card:hover {
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15) !important;
}

.card-title {
    color: var(--text) !important;
    font-size: 1.25rem !important;
    font-weight: 600 !important;
    margin-bottom: 0.75rem !important;
}

.card-subtitle {
    color: var(--text-secondary) !important;
    font-size: 0.9rem !important;
    margin-bottom: 1rem !important;
}

.card-content {
    color: var(--text) !important;
}

/* Улучшенные стили для карточек пользователей и приложений */
.user-tag, .app-tag {
    background-color: var(--secondary-bg);
    color: var(--text);
    padding: 0.5rem 0.75rem;
    border-radius: 1rem;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
    border: 1px solid var(--border);
    display: inline-block;
    font-size: 0.9rem;
    transition: all 0.2s ease;
}

.user-tag:hover, .app-tag:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
}

.user-tag {
    border-color: var(--primary-dark);
}

.app-tag {
    border-color: var(--info);
}

.user-tag span, .app-tag span {
    font-weight: 500;
}

/* Стили для бейджей и меток */
.badge {
    display: inline-block !important;
    padding: 0.35rem 0.65rem !important;
    font-size: 0.75rem !important;
    font-weight: 600 !important;
    line-height: 1 !important;
    text-align: center !important;
    white-space: nowrap !important;
    vertical-align: baseline !important;
    border-radius: 10rem !important;
    margin-right: 0.5rem !important;
}

.badge-primary {
    background-color: var(--primary) !important;
    color: white !important;
}

.badge-success {
    background-color: var(--success) !important;
    color: white !important;
}

.badge-info {
    background-color: var(--info) !important;
    color: white !important;
}

.badge-warning {
    background-color: var(--warning) !important;
    color: black !important;
}

.badge-danger {
    background-color: var(--danger) !important;
    color: white !important;
}

/* Стили для визуальных разделителей */
.divider {
    height: 1px !important;
    background-color: var(--border) !important;
    margin: 1.5rem 0 !important;
}

/* Кастомные стили для компонентов с действиями */
.actions-container {
    background-color: var(--secondary-bg) !important;
    border-radius: var(--radius) !important;
    border: 1px solid var(--border) !important;
    padding: 1.25rem !important;
    margin-bottom: 1.5rem !important;
    box-shadow: var(--shadow) !important;
}

.action-row {
    background-color: rgba(255, 255, 255, 0.05) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
    margin-bottom: 0.75rem !important;
    border: 1px solid rgba(255, 255, 255, 0.1) !important;
}

/* Улучшенные уведомления */
.stAlert {
    border-radius: var(--radius) !important;
    border: none !important;
    padding: 1rem !important;
    margin-bottom: 1rem !important;
    box-shadow: var(--shadow) !important;
}

/* Улучшение метрик */
.stMetric {
    background-color: var(--secondary-bg) !important;
    border-radius: var(--radius) !important;
    padding: 1rem !important;
    box-shadow: var(--shadow) !important;
    border: 1px solid var(--border) !important;
}

.stMetric label {
    color: var(--text-secondary) !important;
    font-weight: 500 !important;
}

.stMetric .metric-value {
    color: var(--text) !important;
    font-size: 2rem !important;
    font-weight: 700 !important;
}

/* Улучшение текстовых стилей */
h1, h2, h3, h4, h5, h6 {
    color: var(--text) !important;
    margin-top: 0.5rem !important;
    margin-bottom: 1rem !important;
}

p, li, a {
    color: var(--text) !important;
}

/* Улучшение отзывчивости колонок */
@media only screen and (max-width: 768px) {
    .block-container {
        max-width: 100% !important;
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    
    .css-18e3th9 {
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }
    
    .css-1y4p8pa {
        padding-left: 0px !important;
        padding-right: 0px !important;
    }
}
</style>
"""

# Добавляем методы для экспорта стилей
def get_modern_styles():
    """Возвращает современные CSS-стили для приложения."""
    return MODERN_STYLES

# Для обратной совместимости
def get_dark_mode_styles():
    """Возвращает CSS-стили для темного режима (устарело)."""
    return MODERN_STYLES 