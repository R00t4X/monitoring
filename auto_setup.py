import subprocess
import sys
import os
import venv
import platform
import importlib.util

class AutoSetup:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.venv_name = "monitoring_venv"
        self.venv_path = os.path.join(self.script_dir, self.venv_name)
        self.is_windows = platform.system() == "Windows"
        
        if self.is_windows:
            self.python_exe = os.path.join(self.venv_path, "Scripts", "python.exe")
            self.pip_exe = os.path.join(self.venv_path, "Scripts", "pip.exe")
        else:
            self.python_exe = os.path.join(self.venv_path, "bin", "python")
            self.pip_exe = os.path.join(self.venv_path, "bin", "pip")
    
    def print_step(self, message):
        print(f"🔧 {message}")
    
    def print_success(self, message):
        print(f"✅ {message}")
    
    def print_error(self, message):
        print(f"❌ {message}")
    
    def print_warning(self, message):
        print(f"⚠️  {message}")
    
    def check_python_version(self):
        """Проверка версии Python"""
        self.print_step("Проверка версии Python...")
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            self.print_error(f"Требуется Python 3.7+, найден {version.major}.{version.minor}")
            return False
        
        self.print_success(f"Python {version.major}.{version.minor}.{version.micro}")
        return True
    
    def create_venv(self):
        """Создание виртуального окружения"""
        if os.path.exists(self.venv_path):
            self.print_success(f"Виртуальное окружение уже существует: {self.venv_name}")
            return True
        
        self.print_step("Создание виртуального окружения...")
        try:
            venv.create(self.venv_path, with_pip=True)
            self.print_success("Виртуальное окружение создано")
            return True
        except Exception as e:
            self.print_error(f"Не удалось создать виртуальное окружение: {e}")
            return False
    
    def upgrade_pip(self):
        """Обновление pip"""
        self.print_step("Обновление pip...")
        try:
            subprocess.run([
                self.python_exe, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True, capture_output=True, text=True)
            self.print_success("pip обновлен")
            return True
        except subprocess.CalledProcessError as e:
            self.print_warning(f"Не удалось обновить pip: {e}")
            return True  # Продолжаем работу
    
    def install_requirements(self):
        """Установка зависимостей"""
        self.print_step("Установка зависимостей...")
        
        # Список необходимых пакетов
        packages = [
            "Flask==2.3.3",
            "Werkzeug==2.3.7",
            "psutil==5.9.6",
            "py-cpuinfo==9.0.0"
        ]
        
        # Создаем requirements.txt если его нет
        req_file = os.path.join(self.script_dir, "requirements.txt")
        if not os.path.exists(req_file):
            with open(req_file, 'w') as f:
                for package in packages:
                    f.write(f"{package}\n")
        
        # Устанавливаем пакеты
        for package in packages:
            try:
                subprocess.run([
                    self.pip_exe, "install", package
                ], check=True, capture_output=True, text=True)
                self.print_success(f"Установлен {package}")
            except subprocess.CalledProcessError as e:
                self.print_error(f"Ошибка установки {package}: {e}")
                return False
        
        return True
    
    def check_imports(self):
        """Проверка импортов"""
        self.print_step("Проверка модулей...")
        
        # Проверяем импорты через subprocess в виртуальном окружении
        test_script = '''
import sys
try:
    import flask
    import psutil
    import cpuinfo
    print("SUCCESS: All modules imported")
except ImportError as e:
    print(f"ERROR: {e}")
    sys.exit(1)
'''
        
        try:
            result = subprocess.run([
                self.python_exe, "-c", test_script
            ], capture_output=True, text=True, check=True)
            
            if "SUCCESS" in result.stdout:
                self.print_success("Все модули доступны")
                return True
            else:
                self.print_error("Не все модули импортированы")
                return False
                
        except subprocess.CalledProcessError as e:
            self.print_error(f"Ошибка проверки модулей: {e}")
            return False
    
    def create_directories(self):
        """Создание необходимых директорий"""
        self.print_step("Создание директорий...")
        
        directories = ["templates", "static"]
        
        for directory in directories:
            dir_path = os.path.join(self.script_dir, directory)
            try:
                if not os.path.exists(dir_path):
                    os.makedirs(dir_path, exist_ok=True)
                    self.print_success(f"Создана директория: {directory}")
                else:
                    self.print_success(f"Директория уже существует: {directory}")
            except Exception as e:
                self.print_error(f"Не удалось создать директорию {directory}: {e}")
                return False
        
        return True
    
    def check_required_files(self):
        """Проверка и создание необходимых файлов"""
        self.print_step("Проверка файлов приложения...")
        
        # Проверяем основные файлы
        required_files = {
            'app.py': self.create_app_file,
            'system_monitor.py': self.create_system_monitor_file,
            'admin.py': self.create_admin_file
        }
        
        for filename, create_func in required_files.items():
            file_path = os.path.join(self.script_dir, filename)
            if not os.path.exists(file_path):
                self.print_step(f"Создание файла {filename}...")
                try:
                    create_func()
                    self.print_success(f"Создан файл: {filename}")
                except Exception as e:
                    self.print_error(f"Ошибка создания {filename}: {e}")
                    return False
            else:
                self.print_success(f"Файл найден: {filename}")
        
        return True
    
    def create_app_file(self):
        """Создание базового app.py если его нет"""
        app_content = '''from flask import Flask, render_template, jsonify
import os
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    return jsonify({
        'статус': 'здоров',
        'сообщение': 'Приложение работает',
        'время': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

if __name__ == '__main__':
    print("🚀 Запуск приложения мониторинга на 127.0.0.1:5000")
    app.run(host='127.0.0.1', port=5000, debug=True)
'''
        with open(os.path.join(self.script_dir, 'app.py'), 'w', encoding='utf-8') as f:
            f.write(app_content)
    
    def create_system_monitor_file(self):
        """Создание базового system_monitor.py если его нет"""
        monitor_content = '''import psutil
import platform
import socket
from datetime import datetime

try:
    from cpuinfo import get_cpu_info
    CPUINFO_AVAILABLE = True
except ImportError:
    CPUINFO_AVAILABLE = False
    def get_cpu_info():
        return {'brand_raw': platform.processor() or 'Unknown'}

class SystemMonitor:
    def __init__(self):
        if CPUINFO_AVAILABLE:
            self.cpu_info = get_cpu_info()
        else:
            self.cpu_info = {'brand_raw': platform.processor() or 'Unknown CPU'}
        self.hostname = socket.gethostname()
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
    
    def get_system_info(self):
        return {
            'hostname': self.hostname,
            'platform': platform.system(),
            'processor': self.cpu_info.get('brand_raw', 'Unknown'),
            'uptime': str(datetime.now() - self.boot_time).split('.')[0]
        }

system_monitor = SystemMonitor()
'''
        with open(os.path.join(self.script_dir, 'system_monitor.py'), 'w', encoding='utf-8') as f:
            f.write(monitor_content)
    
    def create_admin_file(self):
        """Создание базового admin.py если его нет"""
        admin_content = '''from flask import Blueprint

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/')
def dashboard():
    return "Admin Dashboard - В разработке"
'''
        with open(os.path.join(self.script_dir, 'admin.py'), 'w', encoding='utf-8') as f:
            f.write(admin_content)
    
    def create_templates(self):
        """Создание базовых HTML шаблонов"""
        self.print_step("Создание HTML шаблонов...")
        
        templates_dir = os.path.join(self.script_dir, 'templates')
        
        # Создаем базовый index.html
        index_content = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Система Мониторинга</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 800px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            text-align: center;
        }
        h1 { color: #333; margin-bottom: 30px; }
        .status { color: #28a745; font-weight: bold; font-size: 1.2em; }
        .links { margin-top: 30px; }
        .links a {
            display: inline-block;
            margin: 10px;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.3s;
        }
        .links a:hover { background: #5a67d8; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ Система Мониторинга</h1>
        <p class="status">✅ Приложение успешно запущено!</p>
        
        <div class="links">
            <a href="/api/health">🔧 Проверка здоровья</a>
            <a href="/admin">⚙️ Админка</a>
        </div>
        
        <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 8px;">
            <h3>📋 Информация</h3>
            <p>Версия: 1.0.0</p>
            <p>Статус: Активно</p>
            <p>Порт: 5000</p>
        </div>
    </div>
</body>
</html>'''
        
        try:
            index_path = os.path.join(templates_dir, 'index.html')
            with open(index_path, 'w', encoding='utf-8') as f:
                f.write(index_content)
            self.print_success("Создан templates/index.html")
            return True
        except Exception as e:
            self.print_error(f"Ошибка создания шаблонов: {e}")
            return False

    def run_app(self):
        """Запуск приложения"""
        self.print_step("Запуск приложения...")
        
        app_file = os.path.join(self.script_dir, "app.py")
        if not os.path.exists(app_file):
            self.print_error("Файл app.py не найден!")
            return False
        
        print("\n" + "="*60)
        print("🚀 ЗАПУСК ПРИЛОЖЕНИЯ МОНИТОРИНГА")
        print("="*60)
        print("🌐 Откройте браузер: http://127.0.0.1:5000")
        print("🛑 Для остановки нажмите Ctrl+C")
        print("="*60)
        
        try:
            subprocess.run([self.python_exe, app_file], cwd=self.script_dir)
            return True
        except KeyboardInterrupt:
            print("\n🛑 Приложение остановлено")
            return True
        except Exception as e:
            self.print_error(f"Ошибка запуска: {e}")
            return False
    
    def setup_and_run(self):
        """Основная функция настройки и запуска"""
        print("\n" + "="*60)
        print("🚀 АВТОНАСТРОЙКА СИСТЕМЫ МОНИТОРИНГА")
        print("="*60)
        
        steps = [
            ("Проверка Python", self.check_python_version),
            ("Создание виртуального окружения", self.create_venv),
            ("Обновление pip", self.upgrade_pip),
            ("Установка зависимостей", self.install_requirements),
            ("Проверка модулей", self.check_imports),
            ("Создание директорий", self.create_directories),
            ("Проверка файлов", self.check_required_files),
            ("Создание шаблонов", self.create_templates),
        ]
        
        for step_name, step_func in steps:
            try:
                if not step_func():
                    self.print_error(f"Ошибка на этапе: {step_name}")
                    return False
            except Exception as e:
                self.print_error(f"Критическая ошибка на этапе '{step_name}': {e}")
                return False
        
        print("\n✅ Настройка завершена успешно!")
        return self.run_app()

def main():
    setup = AutoSetup()
    try:
        setup.setup_and_run()
    except KeyboardInterrupt:
        print("\n🛑 Настройка прервана пользователем")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
