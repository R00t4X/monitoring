import subprocess
import sys
import os

def install_dependencies():
    """Автоматическая установка зависимостей"""
    print("Установка зависимостей...")
    try:
        # Обновляем pip
        subprocess.check_call([sys.executable, "-m", "pip", "install", "--upgrade", "pip"])
        
        # Устанавливаем зависимости из requirements.txt
        if os.path.exists("requirements.txt"):
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        else:
            # Устанавливаем основные зависимости напрямую
            dependencies = ["Flask==2.3.3", "Werkzeug==2.3.7"]
            for dep in dependencies:
                subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
        
        print("✅ Все зависимости успешно установлены!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Ошибка при установке зависимостей: {e}")
        return False

def run_application():
    """Запуск Flask приложения"""
    print("Запуск приложения...")
    try:
        from app import app
        print("🚀 Приложение запущено! Откройте http://127.0.0.1:5000 в браузере")
        app.run(host='127.0.0.1', port=5000, debug=True)
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("Убедитесь, что файл app.py существует в текущей директории")
    except Exception as e:
        print(f"❌ Ошибка запуска приложения: {e}")

if __name__ == "__main__":
    print("🔧 Автоматическая настройка и запуск приложения мониторинга")
    print("=" * 60)
    
    # Установка зависимостей
    if install_dependencies():
        print("\n" + "=" * 60)
        # Запуск приложения
        run_application()
    else:
        print("❌ Не удалось установить зависимости. Запуск отменен.")
        sys.exit(1)
