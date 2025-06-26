#!/usr/bin/env python3
"""
Продвинутая настройка и установка системы мониторинга.
"""
import subprocess
import sys
import os
import venv
import platform

def create_virtual_env():
    """Создание виртуального окружения."""
    print("🔧 Создание виртуального окружения...")
    
    venv_path = "monitoring_venv"
    if not os.path.exists(venv_path):
        venv.create(venv_path, with_pip=True)
        print("✅ Виртуальное окружение создано")
    else:
        print("✅ Виртуальное окружение уже существует")
    
    return venv_path

def install_dependencies(venv_path):
    """Установка зависимостей."""
    print("📦 Установка зависимостей...")
    
    if platform.system() == "Windows":
        pip_path = os.path.join(venv_path, "Scripts", "pip.exe")
    else:
        pip_path = os.path.join(venv_path, "bin", "pip")
    
    # Обновление pip
    subprocess.run([pip_path, "install", "--upgrade", "pip"], check=True)
    
    # Установка зависимостей
    subprocess.run([pip_path, "install", "-r", "requirements.txt"], check=True)
    print("✅ Зависимости установлены")

def create_directories():
    """Создание необходимых директорий."""
    print("📁 Создание директорий...")
    
    directories = [
        'app/controllers',
        'app/models', 
        'app/services/monitoring',
        'app/services/alerts',
        'app/utils',
        'config',
        'logs',
        'templates',
        'static'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Директории созданы")

def create_init_files():
    """Создание __init__.py файлов."""
    print("📝 Создание __init__.py файлов...")
    
    init_files = [
        'app/__init__.py',
        'app/controllers/__init__.py',
        'app/models/__init__.py',
        'app/services/__init__.py',
        'app/services/monitoring/__init__.py',
        'app/services/alerts/__init__.py',
        'app/utils/__init__.py'
    ]
    
    for init_file in init_files:
        if not os.path.exists(init_file):
            with open(init_file, 'w') as f:
                f.write('# -*- coding: utf-8 -*-\n')
    
    print("✅ __init__.py файлы созданы")

def main():
    """Основная функция установки."""
    print("🚀 УСТАНОВКА ПРОДВИНУТОЙ СИСТЕМЫ МОНИТОРИНГА")
    print("=" * 50)
    
    try:
        venv_path = create_virtual_env()
        create_directories()
        create_init_files()
        install_dependencies(venv_path)
        
        print("\n✅ Установка завершена успешно!")
        print("\nДля запуска выполните:")
        if platform.system() == "Windows":
            print(f"   {venv_path}\\Scripts\\activate")
        else:
            print(f"   source {venv_path}/bin/activate")
        print("   python run.py")
        
    except Exception as e:
        print(f"\n❌ Ошибка установки: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
