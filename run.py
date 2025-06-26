#!/usr/bin/env python3
"""
Запуск системы мониторинга.
"""
import os
import sys

def main():
    print("🚀 СИСТЕМА МОНИТОРИНГА")
    print("🌐 http://127.0.0.1:5000")
    print("👤 Админка: admin/admin123")
    print("🛑 Ctrl+C для остановки")
    
    # Добавляем src в путь
    src_path = os.path.join(os.path.dirname(__file__), 'src')
    sys.path.insert(0, src_path)
    
    try:
        from app import app
        app.run(host='127.0.0.1', port=5001, debug=True)
    except ImportError as e:
        print(f"❌ Ошибка: {e}")
        print("📦 Установите: pip install flask psutil")
    except KeyboardInterrupt:
        print("\n🛑 Остановлено")

if __name__ == "__main__":
    main()
