#!/bin/bash

# Параметры удаленного сервера
REMOTE_USER="kiril"
REMOTE_HOST="badkiko.ru"
REMOTE_PORT="44"
REMOTE_PASSWORD="kirill2906042004"
REMOTE_DIR="E:\\Work\\permify"
IMAGE_NAME="permify-ui"
IMAGE_TAG="latest"

# Установка кодировки для корректного отображения русских символов
export LC_ALL=ru_RU.UTF-8 2>/dev/null || export LC_ALL=C.UTF-8 2>/dev/null || true

# Локальная директория для сохранения образа
LOCAL_DIR="$HOME/docker-images"
mkdir -p $LOCAL_DIR

# Флаг использования SSH ключа вместо пароля
USE_SSH_KEY=false

# Функция для отображения статуса
function show_step {
    echo -e "\n\033[1;34m=== $1 ===\033[0m"
}

# Функция проверки ошибок
function check_error {
    if [ $? -ne 0 ]; then
        echo -e "\033[1;31mОШИБКА: $1\033[0m"
        read -p "Продолжить выполнение скрипта? (y/n): " CONTINUE
        if [ "$CONTINUE" != "y" ]; then
            echo "Прерываю выполнение..."
            exit 1
        fi
        echo "Продолжаю выполнение..."
    fi
}

# Функция для выполнения scp с или без пароля
function secure_copy {
    local SOURCE=$1
    local DEST=$2
    
    if [ "$USE_SSH_KEY" = true ]; then
        scp -P $REMOTE_PORT "$SOURCE" "$DEST"
    else
        sshpass -p "$REMOTE_PASSWORD" scp -P $REMOTE_PORT "$SOURCE" "$DEST"
    fi
}

# Функция для выполнения ssh с или без пароля
function secure_shell {
    local CMD=$1
    
    if [ "$USE_SSH_KEY" = true ]; then
        ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "$CMD"
    else
        sshpass -p "$REMOTE_PASSWORD" ssh -p $REMOTE_PORT $REMOTE_USER@$REMOTE_HOST "$CMD"
    fi
}

show_step "Архивация проекта"
echo "Создание архива проекта..."
tar --exclude='project.tar.gz' -czf project.tar.gz .
check_error "Не удалось создать архив проекта"
echo "Архив создан: $(du -h project.tar.gz | cut -f1)"

show_step "Отправка проекта на удаленный сервер"
echo "Передача файла на удаленный сервер..."

# Создаем директорию на удаленном сервере, если она не существует
secure_shell "cmd /c \"mkdir \"$REMOTE_DIR\" 2>nul\""

# Копируем архив напрямую в целевую директорию
secure_copy "project.tar.gz" "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/project.tar.gz"
check_error "Не удалось передать файл на удаленный сервер"

show_step "Проверка состояния Docker на удаленном сервере"
DOCKER_RUNNING=$(secure_shell "cmd /c \"docker info >nul 2>&1 && echo yes || echo no\"")

if [ "$DOCKER_RUNNING" = "no" ]; then
    echo -e "\033[1;31mВнимание! Docker не запущен на удаленном сервере!\033[0m"
    echo "Пожалуйста, запустите Docker Desktop на удаленном сервере и повторите попытку."
    
    read -p "Продолжить выполнение скрипта несмотря на это? (y/n): " CONTINUE
    if [ "$CONTINUE" != "y" ]; then
        echo "Прерываю выполнение..."
        exit 1
    fi
    echo "Продолжаю выполнение..."
else
    echo -e "\033[1;32mDocker успешно запущен на удаленном сервере.\033[0m"
fi

show_step "Выполнение команд на удаленном сервере"
echo "Распаковка архива и сборка Docker образа..."

secure_shell "cmd /c \"
chcp 65001 >nul
cd \"$REMOTE_DIR\"
echo Распаковка архива...
tar -xf project.tar.gz
echo Сборка Docker образа...
docker build -t $IMAGE_NAME:$IMAGE_TAG .
if %ERRORLEVEL% neq 0 (
  echo Ошибка при сборке образа!
  exit 1
)
echo Сохранение Docker образа...
docker save -o docker-image.tar $IMAGE_NAME:$IMAGE_TAG
if %ERRORLEVEL% neq 0 (
  echo Ошибка при сохранении образа!
  exit 1
)
exit 0
\""
check_error "Ошибка при выполнении команд на удаленном сервере"

show_step "Загрузка образа с удаленного сервера"
echo "Проверка наличия образа на удаленном сервере..."
FILE_EXISTS=$(secure_shell "cmd /c \"chcp 65001 >nul && if exist \"$REMOTE_DIR\\docker-image.tar\" (echo yes) else (echo no)\"")

if [ "$FILE_EXISTS" = "yes" ]; then
    echo "Образ найден, загружаю..."
    secure_copy "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DIR/docker-image.tar" "$LOCAL_DIR/docker-image.tar"
    check_error "Не удалось загрузить образ с удаленного сервера"
    echo "Образ загружен: $(du -h $LOCAL_DIR/docker-image.tar | cut -f1)"
else
    echo -e "\033[1;31mОшибка: Файл образа на удаленном сервере не существует!\033[0m"
    exit 1
fi

show_step "Загрузка Docker образа локально"
echo "Загрузка образа в локальный Docker..."
docker load < $LOCAL_DIR/docker-image.tar
check_error "Не удалось загрузить образ в локальный Docker"

echo -e "\n\033[1;32mГотово! Образ $IMAGE_NAME:$IMAGE_TAG доступен локально.\033[0m"