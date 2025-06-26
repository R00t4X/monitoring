#!/usr/bin/env python3
"""
Быстрый запуск системы мониторинга
Создает все необходимые файлы и запускает приложение
"""

import os
import sys
import subprocess
import platform

def main():
    print("🚀 БЫСТРЫЙ ЗАПУСК СИСТЕМЫ МОНИТОРИНГА")
    print("=" * 50)
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Определяем команду Python
    if platform.system() == "Windows":
        python_cmd = "python"
    else:
        python_cmd = "python3"
    
    # Проверяем Python
    try:
        result = subprocess.run([python_cmd, "--version"], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Найден Python: {result.stdout.strip()}")
        else:
            print("❌ Python не найден!")
            return False
    except FileNotFoundError:
        print("❌ Python не установлен или недоступен!")
        return False
    
    print("\n🔧 Запуск автонастройки...")
    
    # Запускаем автонастройку
    try:
        # Используем текущий интерпретатор Python
        subprocess.run([sys.executable, "-c", """
import subprocess
import sys
import os
import venv

print("🔧 Автоматическая настройка...")

# Создаем виртуальное окружение
venv_path = "monitoring_venv"
if not os.path.exists(venv_path):
    print("📦 Создание виртуального окружения...")
    venv.create(venv_path, with_pip=True)

# Определяем пути
if os.name == 'nt':  # Windows
    python_exe = os.path.join(venv_path, "Scripts", "python.exe")
    pip_exe = os.path.join(venv_path, "Scripts", "pip.exe")
else:  # Unix/Linux/macOS
    python_exe = os.path.join(venv_path, "bin", "python")
    pip_exe = os.path.join(venv_path, "bin", "pip")

# Устанавливаем зависимости
packages = ["Flask==2.3.3", "psutil==5.9.6", "py-cpuinfo==9.0.0"]
for package in packages:
    print(f"📥 Установка {package}...")
    subprocess.run([pip_exe, "install", package], 
                  capture_output=True, check=True)

print("✅ Настройка завершена!")

# Создаем минимальное приложение если app.py не существует
if not os.path.exists("app.py"):
    print("📝 Создание базового приложения...")
    app_code = '''
from flask import Flask, jsonify, render_template_string
from datetime import datetime
import os

app = Flask(__name__)

HTML_TEMPLATE = \"\"\"
<!DOCTYPE html>
<html>
<head><title>Система Мониторинга</title>
<style>
body{font-family:Arial;max-width:800px;margin:50px auto;padding:20px;background:linear-gradient(135deg,#667eea 0%,#764ba2 100%);min-height:100vh}
.container{background:white;padding:40px;border-radius:15px;box-shadow:0 10px 30px rgba(0,0,0,0.2);text-align:center}
h1{color:#333;margin-bottom:30px}.status{color:#28a745;font-weight:bold;font-size:1.2em}
.info{margin-top:30px;padding:20px;background:#f8f9fa;border-radius:8px}
</style></head>
<body>
<div class="container">
<h1>🖥️ Система Мониторинга</h1>
<p class="status">✅ Приложение успешно запущено!</p>
<div class="info">
<h3>📋 Информация</h3>
<p>Время запуска: {{ time }}</p>
<p>Статус: Активно</p>
<p>Порт: 5000</p>
</div>
</div>
</body>
</html>
\"\"\"

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE, 
                                time=datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/health')
def health():
    return jsonify({
        'status': 'healthy',
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'message': 'Приложение работает'
    })

if __name__ == '__main__':
    print("🚀 Запуск на http://127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
'''
    with open("app.py", "w", encoding="utf-8") as f:
        f.write(app_code)

# Запускаем приложение
print("🚀 Запуск приложения...")
subprocess.run([python_exe, "app.py"])
"""], cwd=script_dir)
        
    except KeyboardInterrupt:
        print("\n🛑 Запуск прерван")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 Программа прервана")
    finally:
        if platform.system() == "Windows":
            input("Нажмите Enter для выхода...")
