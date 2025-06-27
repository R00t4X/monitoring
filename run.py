#!/usr/bin/env python3
"""
Автоматическая настройка и запуск системы мониторинга.
Объединяет функции установки зависимостей, создания виртуального окружения и запуска приложения.
"""
import subprocess
import sys
import os
import venv
import importlib.util

def check_package_installed(package_name):
    """Проверка, установлен ли пакет"""
    spec = importlib.util.find_spec(package_name)
    return spec is not None

def install_package(package, python_exe=None):
    """Установка пакета через pip"""
    if python_exe is None:
        python_exe = sys.executable
    
    try:
        subprocess.run([python_exe, "-m", "pip", "install", package], 
                      check=True, capture_output=True, text=True)
        print(f"✅ {package} установлен")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка установки {package}: {e}")
        return False

def check_python_version():
    """Проверка версии Python"""
    if sys.version_info < (3, 7):
        print("❌ Требуется Python 3.7 или выше")
        print(f"   Текущая версия: {sys.version}")
        sys.exit(1)
    else:
        print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

def setup_virtual_environment():
    """Создание и настройка виртуального окружения"""
    print("\n🔧 НАСТРОЙКА ВИРТУАЛЬНОГО ОКРУЖЕНИЯ")
    print("=" * 40)
    
    venv_path = "venv"
    
    # Создаем виртуальное окружение
    if not os.path.exists(venv_path):
        print("📦 Создание виртуального окружения...")
        try:
            venv.create(venv_path, with_pip=True)
            print("✅ Виртуальное окружение создано")
        except Exception as e:
            print(f"❌ Ошибка создания виртуального окружения: {e}")
            return None, None
    else:
        print("✅ Виртуальное окружение уже существует")
    
    # Определяем путь к python и pip
    if os.name == 'nt':  # Windows
        python_exe = os.path.join(venv_path, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
    else:  # Linux/Mac
        python_exe = os.path.join(venv_path, "bin", "python")
        pip_exe = os.path.join(venv_path, "bin", "pip")
    
    # Проверяем, что исполняемые файлы существуют
    if not os.path.exists(python_exe):
        print(f"❌ Python исполняемый файл не найден: {python_exe}")
        return None, None
    
    return python_exe, pip_exe

def install_dependencies(python_exe=None):
    """Установка всех необходимых зависимостей"""
    print("\n📦 УСТАНОВКА ЗАВИСИМОСТЕЙ")
    print("=" * 30)
    
    # Пакеты из requirements.txt
    packages = [
        'Flask==2.3.3',
        'psutil==5.9.6', 
        'py-cpuinfo==9.0.0',
        'paramiko==3.4.0'
    ]
    
    success_count = 0
    for package in packages:
        if install_package(package, python_exe):
            success_count += 1
    
    print(f"\n✅ Установлено {success_count}/{len(packages)} пакетов")
    return success_count >= len(packages) - 1  # Хотя бы Flask и основные пакеты

def check_dependencies():
    """Проверка наличия необходимых зависимостей"""
    required_packages = ['flask', 'psutil', 'cpuinfo', 'paramiko']
    missing_packages = []
    
    for package in required_packages:
        if not check_package_installed(package):
            missing_packages.append(package)
    
    return missing_packages

def run_application(python_exe=None):
    """Запуск приложения"""
    # Проверяем доступный порт
    port = int(os.environ.get('PORT', 5001))
    
    # Проверяем доступность порта
    import socket
    for check_port in range(port, port + 10):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', check_port)) != 0:
                port = check_port
                break
    
    print("\n🚀 ЗАПУСК СИСТЕМЫ МОНИТОРИНГА")
    print("=" * 35)
    print(f"🌐 http://127.0.0.1:{port}")
    print("👤 Админка: войдите с учетными данными")
    print("� Автомониторинг: каждые 60 секунд")
    print("�🛑 Ctrl+C для остановки")
    print()
    
    # Добавляем src в путь
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    sys.path.insert(0, src_path)
    
    try:
        if python_exe and python_exe != sys.executable:
            # Запускаем через виртуальное окружение
            app_script = f"""
import sys
import os
sys.path.insert(0, '{src_path}')
from app import app, scheduler

# Запускаем планировщик с интервалом 60 секунд
scheduler.start(interval=60)
print("🔄 Автоматический мониторинг запущен (интервал: 60 секунд)")

app.run(host='127.0.0.1', port={port}, debug=True)
"""
            with open('temp_run_app.py', 'w') as f:
                f.write(app_script)
            
            try:
                subprocess.run([python_exe, 'temp_run_app.py'], check=True)
            finally:
                if os.path.exists('temp_run_app.py'):
                    os.remove('temp_run_app.py')
        else:
            # Запускаем в текущем окружении
            from app import app, scheduler
            
            # Запускаем планировщик с интервалом 60 секунд
            scheduler.start(interval=60)
            print("🔄 Автоматический мониторинг запущен (интервал: 60 секунд)")
            
            app.run(host='127.0.0.1', port=port, debug=True)
            
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("📦 Проверьте установку зависимостей")
        return False
    except KeyboardInterrupt:
        print("\n🛑 Система мониторинга остановлена")
        return True
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        return False

def main():
    """Основная функция - автоматическая настройка и запуск"""
    print("🔧 АВТОМАТИЧЕСКАЯ НАСТРОЙКА СИСТЕМЫ МОНИТОРИНГА")
    print("=" * 50)
    
    # 1. Проверяем версию Python
    check_python_version()
    
    # 2. Проверяем наличие зависимостей
    missing_packages = check_dependencies()
    use_venv = False
    python_exe = sys.executable
    
    if missing_packages:
        print(f"\n⚠️  Отсутствующие пакеты: {', '.join(missing_packages)}")
        
        # Пытаемся установить в текущем окружении
        print("\n🔄 Попытка установки в текущем окружении...")
        if not install_dependencies():
            print("\n🔄 Создание виртуального окружения...")
            # Создаем виртуальное окружение
            venv_python, venv_pip = setup_virtual_environment()
            if venv_python:
                if install_dependencies(venv_python):
                    python_exe = venv_python
                    use_venv = True
                    print("✅ Зависимости установлены в виртуальном окружении")
                else:
                    print("❌ Не удалось установить зависимости")
                    sys.exit(1)
            else:
                print("❌ Не удалось создать виртуальное окружение")
                sys.exit(1)
    else:
        print("✅ Все зависимости уже установлены")
    
    # 3. Запускаем приложение
    if use_venv:
        print(f"\n📝 Используется виртуальное окружение: {os.path.dirname(python_exe)}")
    
    run_application(python_exe if use_venv else None)

if __name__ == "__main__":
    main()
