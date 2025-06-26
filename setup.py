#!/usr/bin/env python3
"""
Быстрая настройка и запуск системы мониторинга.
"""
import subprocess
import sys
import os

def main():
    print("🔧 БЫСТРАЯ НАСТРОЙКА СИСТЕМЫ МОНИТОРИНГА")
    print("=" * 45)
    
    # Проверяем Python версию
    if sys.version_info < (3, 7):
        print("❌ Требуется Python 3.7 или выше")
        sys.exit(1)
    
    print("✅ Python версия подходит")
    
    # Устанавливаем зависимости
    try:
        print("📦 Установка зависимостей...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], 
                      check=True, capture_output=True)
        print("✅ Зависимости установлены")
    except subprocess.CalledProcessError:
        print("⚠️ Ошибка установки зависимостей, но продолжаем...")
    
    # Запускаем приложение
    print("\n🚀 Запуск приложения...")
    try:
        subprocess.run([sys.executable, "run_app.py"])
    except KeyboardInterrupt:
        print("\n🛑 Остановлено пользователем")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

if __name__ == "__main__":
    main()
