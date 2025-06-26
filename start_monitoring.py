#!/usr/bin/env python3
"""
Единая точка входа для запуска системы мониторинга.
"""
import os
import sys

def main():
    print("🚀 СИСТЕМА МОНИТОРИНГА")
    print("=" * 40)
    
    # Проверяем наличие файлов
    if os.path.exists('simple_app.py'):
        print("✅ Найден simple_app.py - запуск основного приложения")
        try:
            from simple_app import app
            app.run(host='127.0.0.1', port=5000, debug=True)
        except ImportError as e:
            print(f"❌ Ошибка импорта: {e}")
    else:
        print("❌ Файл simple_app.py не найден!")
        print("📋 Убедитесь, что вы находитесь в правильной директории")

if __name__ == "__main__":
    main()
