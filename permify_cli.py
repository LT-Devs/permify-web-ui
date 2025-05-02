#!/usr/bin/env python3
import os
import subprocess
import argparse
import tempfile
import shutil

def run_permify_command(command, files=None):
    """Запускает команду Permify CLI через Docker"""
    try:
        # Создаем временную директорию для файлов
        temp_dir = tempfile.mkdtemp()
        mounted_files = []
        
        # Копируем файлы во временную директорию
        if files:
            for file_path in files:
                if os.path.exists(file_path):
                    file_name = os.path.basename(file_path)
                    dest_path = os.path.join(temp_dir, file_name)
                    shutil.copy2(file_path, dest_path)
                    mounted_files.append((file_path, f"/data/{file_name}"))
                else:
                    print(f"Файл {file_path} не найден!")
                    return None
        
        # Строим команду Docker
        docker_cmd = [
            "docker", "run", "--rm", 
            "-v", f"{temp_dir}:/data",
            "--network=host",
            "permify/permify:latest"
        ]
        
        # Добавляем команду Permify
        full_command = docker_cmd + command
        
        # Подставляем пути к файлам внутри контейнера
        for i, arg in enumerate(full_command):
            for file_path, container_path in mounted_files:
                if arg == file_path:
                    full_command[i] = container_path
        
        # Выполняем команду
        print(f"Выполняем: {' '.join(full_command)}")
        result = subprocess.run(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0:
            print(f"Ошибка выполнения команды: {result.stderr}")
        
        return result
    finally:
        # Очищаем временную директорию
        shutil.rmtree(temp_dir)

def main():
    parser = argparse.ArgumentParser(description='Permify CLI Helper')
    subparsers = parser.add_subparsers(dest='command', help='Команда')
    
    # Команда для загрузки схемы
    schema_parser = subparsers.add_parser('schema', help='Работа со схемой')
    schema_parser.add_argument('--file', required=True, help='Путь к файлу схемы')
    schema_parser.add_argument('--validate', action='store_true', help='Только валидировать схему')
    
    # Команда для проверки соединения
    ping_parser = subparsers.add_parser('ping', help='Проверка соединения с Permify')
    
    # Команда для запуска Permify локально
    serve_parser = subparsers.add_parser('serve', help='Запуск Permify сервера')
    
    args = parser.parse_args()
    
    if args.command == 'schema':
        if args.validate:
            result = run_permify_command(['validate', args.file], [args.file])
            if result and result.returncode == 0:
                print("Схема валидна!")
                print(result.stdout)
            else:
                print("Схема невалидна!")
        else:
            # Здесь в будущем можно добавить загрузку схемы через API
            print("Для загрузки схемы используйте:")
            print("curl -X POST -H 'Content-Type: text/plain' --data-binary @schema.perm http://localhost:9010/v1/tenants/t1/schemas")
            print("или воспользуйтесь интерфейсом Streamlit (streamlit run permify_app.py)")
    
    elif args.command == 'ping':
        print("Проверка соединения с Permify...")
        subprocess.run(["curl", "-s", "http://localhost:9010/healthz"])
        print("\nПроверка gRPC порта...")
        subprocess.run(["nc", "-zv", "localhost", "9011"])
    
    elif args.command == 'serve':
        print("Запуск Permify сервера...")
        run_permify_command(['serve'])
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main() 