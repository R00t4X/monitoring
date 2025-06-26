#!/usr/bin/env python3
"""
Создание виртуального окружения и установка зависимостей.
"""
import subprocess
import sys
import os
import venv

def main():
    print("🔧 СОЗДАНИЕ ВИРТУАЛЬНОГО ОКРУЖЕНИЯ")
    print("=" * 40)
    
    venv_path = "monitoring_venv"
    
    # Создаем виртуальное окружение
    if not os.path.exists(venv_path):
        print("📦 Создание виртуального окружения...")
        venv.create(venv_path, with_pip=True)
        print("✅ Виртуальное окружение создано")
    else:
        print("✅ Виртуальное окружение уже существует")
    
    # Определяем путь к python и pip
    if os.name == 'nt':  # Windows
        python_exe = os.path.join(venv_path, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
    else:  # Linux/Mac
        python_exe = os.path.join(venv_path, "bin", "python")
        pip_exe = os.path.join(venv_path, "bin", "pip")
    
    # Устанавливаем зависимости
    packages = ['flask', 'psutil', 'py-cpuinfo', 'paramiko']
    
    for package in packages:
        try:
            print(f"📦 Установка {package}...")
            subprocess.run([pip_exe, "install", package], check=True, capture_output=True)
            print(f"✅ {package} установлен")
        except subprocess.CalledProcessError:
            print(f"❌ Ошибка установки {package}")
    
    print(f"\n🚀 Для запуска используйте:")
    print(f"   {python_exe} run.py")

if __name__ == "__main__":
    main()
