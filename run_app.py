#!/usr/bin/env python3
"""
Единственный файл запуска системы мониторинга.
"""
import os
import sys
import logging

# Добавляем корневую директорию в PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Создаем необходимые директории
os.makedirs('data', exist_ok=True)
os.makedirs('logs', exist_ok=True)

def main():
    """Запуск приложения."""
    print("🚀 СИСТЕМА МОНИТОРИНГА")
    print("=" * 40)
    
    try:
        from web.app import app
        app.run(host='127.0.0.1', port=5000, debug=True)
    except ImportError as e:
        print(f"❌ Ошибка: {e}")
        print("🔧 Установите: pip install flask psutil")
        sys.exit(1)

if __name__ == "__main__":
    main()
        import flask
    except ImportError:
        missing.append('flask')
    
    if missing:
        print("❌ Отсутствуют критические зависимости:")
        for dep in missing:
            print(f"   - {dep}")
        print("\n🔧 Для автоустановки запустите:")
        print("   python -m utils.installer")
        return False
    return True

def main():
    """Запуск приложения мониторинга."""
    print("🚀 СИСТЕМА МОНИТОРИНГА")
    print("=" * 40)
    
    if not check_dependencies():
        sys.exit(1)
    
    try:
        from web.app import app
        
        # Получаем параметры запуска
        host = os.environ.get("HOST", "127.0.0.1")
        port = int(os.environ.get("PORT", 5000))
        debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
        
        print(f"🚀 Запуск приложения на {host}:{port}")
        print(f"🌐 Откройте браузер: http://{host}:{port}")
        print("📊 Доступные разделы:")
        print("   / - Главная страница")
        print("   /servers - Мониторинг серверов") 
        print("   /system - Системный мониторинг")
        print("   /admin - Админка (admin/admin123)")
        print("🛑 Для остановки нажмите Ctrl+C")
        print("=" * 40)
        
        app.run(host=host, port=port, debug=debug)
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("📦 Возможно, не установлены зависимости")
        print("🔧 Запустите: python -m utils.installer")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Приложение остановлено пользователем")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
