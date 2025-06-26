#!/usr/bin/env python3
"""
Простой запуск системы мониторинга с автонастройкой
"""

import os
import sys
import subprocess

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    print("🚀 СИСТЕМА МОНИТОРИНГА")
    print("=" * 40)
    
    # Проверяем наличие auto_setup.py
    auto_setup_path = os.path.join(script_dir, "auto_setup.py")
    if not os.path.exists(auto_setup_path):
        print("❌ Файл auto_setup.py не найден!")
        print("📁 Убедитесь, что все файлы находятся в одной папке")
        input("Нажмите Enter для выхода...")
        sys.exit(1)
    
    # Запускаем автонастройку
    try:
        python_cmd = sys.executable
        result = subprocess.run([python_cmd, auto_setup_path], cwd=script_dir)
        
        if result.returncode != 0:
            print(f"\n❌ Автонастройка завершилась с ошибкой (код: {result.returncode})")
        else:
            print("\n✅ Автонастройка завершена успешно!")
            
    except KeyboardInterrupt:
        print("\n🛑 Запуск прерван пользователем")
    except Exception as e:
        print(f"❌ Критическая ошибка: {e}")
    
    input("\nНажмите Enter для выхода...")

if __name__ == "__main__":
    main()
