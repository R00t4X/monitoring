#!/usr/bin/env python3
"""
Установка зависимостей для системы мониторинга.
"""
import subprocess
import sys
import os

def install_package(package):
    """Установка пакета через pip"""
    try:
        subprocess.run([sys.executable, "-m", "pip", "install", package], 
                      check=True, capture_output=True)
        print(f"✅ {package} установлен")
        return True
    except subprocess.CalledProcessError:
        print(f"❌ Ошибка установки {package}")
        return False

def main():
    print("📦 УСТАНОВКА ЗАВИСИМОСТЕЙ")
    print("=" * 30)
    
    packages = ['flask', 'psutil', 'py-cpuinfo', 'paramiko']
    
    success_count = 0
    for package in packages:
        if install_package(package):
            success_count += 1
    
    print(f"\n✅ Установлено {success_count}/{len(packages)} пакетов")
    
    if success_count >= 1:  # Хотя бы Flask
        print("\n🚀 Запустите: python3 run.py")
    else:
        print("\n❌ Установка не удалась")

if __name__ == "__main__":
    main()
