import os
import sys

# Проверяем, запущены ли мы в виртуальном окружении
def is_venv():
    return hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )

def main():
    # Если не в виртуальном окружении, запускаем автонастройку
    if not is_venv():
        print("🔧 Не обнаружено виртуальное окружение")
        print("🚀 Запуск автонастройки...")
        
        # Импортируем и запускаем автонастройку
        try:
            from auto_setup import AutoSetup
            setup = AutoSetup()
            setup.setup_and_run()
        except ImportError:
            print("❌ Файл auto_setup.py не найден!")
            print("📥 Запустите: python3 auto_setup.py")
            sys.exit(1)
    else:
        # Если в виртуальном окружении, просто импортируем и запускаем app
        try:
            from app import app
            print("🚀 Запуск приложения из виртуального окружения...")
            app.run(debug=True, host='127.0.0.1', port=5000)
        except ImportError as e:
            print(f"❌ Ошибка импорта: {e}")
            print("🔧 Попробуйте переустановить зависимости")
            sys.exit(1)

if __name__ == '__main__':
    main()
