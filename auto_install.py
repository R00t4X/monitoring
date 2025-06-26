#!/usr/bin/env python3
"""
Автоматическая установка всех зависимостей и запуск приложения.
"""
import subprocess
import sys
import os
import venv
import platform
import importlib

class AutoInstaller:
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
    
    def print_status(self, message, status="INFO"):
        icons = {"INFO": "ℹ️", "SUCCESS": "✅", "ERROR": "❌", "WARNING": "⚠️"}
        print(f"{icons.get(status, 'ℹ️')} {message}")
    
    def check_python_version(self):
        """Проверка версии Python"""
        self.print_status("Проверка версии Python...")
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            self.print_status(f"Требуется Python 3.7+, найден {version.major}.{version.minor}", "ERROR")
            return False
        
        self.print_status(f"Python {version.major}.{version.minor}.{version.micro} - OK", "SUCCESS")
        return True
    
    def create_venv(self):
        """Создание виртуального окружения"""
        if os.path.exists(self.venv_path):
            self.print_status("Виртуальное окружение уже существует", "SUCCESS")
            return True
        
        self.print_status("Создание виртуального окружения...")
        try:
            venv.create(self.venv_path, with_pip=True)
            self.print_status("Виртуальное окружение создано", "SUCCESS")
            return True
        except Exception as e:
            self.print_status(f"Ошибка создания виртуального окружения: {e}", "ERROR")
            return False
    
    def upgrade_pip(self):
        """Обновление pip"""
        self.print_status("Обновление pip...")
        try:
            subprocess.run([
                self.python_exe, "-m", "pip", "install", "--upgrade", "pip"
            ], check=True, capture_output=True, text=True, timeout=120)
            self.print_status("pip обновлен", "SUCCESS")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self.print_status(f"Предупреждение: не удалось обновить pip: {e}", "WARNING")
            return True  # Продолжаем без обновления pip
    
    def install_package(self, package_name, version=None):
        """Установка отдельного пакета"""
        package_spec = f"{package_name}=={version}" if version else package_name
        
        try:
            # Проверяем, установлен ли уже пакет
            result = subprocess.run([
                self.python_exe, "-c", f"import {package_name}"
            ], capture_output=True, text=True)
            
            if result.returncode == 0:
                self.print_status(f"{package_name} уже установлен", "SUCCESS")
                return True
        except:
            pass
        
        self.print_status(f"Установка {package_spec}...")
        try:
            subprocess.run([
                self.pip_exe, "install", package_spec, "--timeout", "120"
            ], check=True, capture_output=True, text=True, timeout=180)
            self.print_status(f"{package_name} установлен", "SUCCESS")
            return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self.print_status(f"Ошибка установки {package_name}: {e}", "ERROR")
            return False
    
    def install_dependencies(self):
        """Установка всех зависимостей"""
        self.print_status("Установка зависимостей...")
        
        # Основные пакеты
        packages = [
            ("flask", "2.3.3"),
            ("werkzeug", "2.3.7"),
            ("psutil", "5.9.6"),
            ("py-cpuinfo", "9.0.0")
        ]
        
        success_count = 0
        for package_name, version in packages:
            if self.install_package(package_name, version):
                success_count += 1
        
        if success_count >= 2:  # Минимум Flask и один из мониторинг пакетов
            self.print_status(f"Установлено {success_count}/{len(packages)} пакетов", "SUCCESS")
            return True
        else:
            self.print_status("Критическая ошибка: не установлены основные пакеты", "ERROR")
            return False
    
    def verify_installation(self):
        """Проверка установки"""
        self.print_status("Проверка установленных модулей...")
        
        test_script = '''
import sys
modules_status = {}

# Проверяем Flask (обязательный)
try:
    import flask
    modules_status["flask"] = "OK"
except ImportError as e:
    modules_status["flask"] = f"ERROR: {e}"
    sys.exit(1)

# Проверяем psutil (желательный)
try:
    import psutil
    modules_status["psutil"] = "OK"
except ImportError:
    modules_status["psutil"] = "NOT_AVAILABLE"

# Проверяем cpuinfo (желательный)
try:
    import cpuinfo
    modules_status["cpuinfo"] = "OK"
except ImportError:
    modules_status["cpuinfo"] = "NOT_AVAILABLE"

# Выводим результаты
for module, status in modules_status.items():
    print(f"{module}: {status}")

print("VERIFICATION_SUCCESS")
'''
        
        try:
            result = subprocess.run([
                self.python_exe, "-c", test_script
            ], capture_output=True, text=True, check=True, timeout=30)
            
            print(result.stdout)
            if "VERIFICATION_SUCCESS" in result.stdout:
                self.print_status("Проверка модулей завершена", "SUCCESS")
                return True
            else:
                self.print_status("Ошибка проверки модулей", "ERROR")
                return False
                
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            self.print_status(f"Ошибка проверки: {e}", "ERROR")
            return False
    
    def create_requirements_file(self):
        """Создание файла requirements.txt"""
        requirements_content = """# Зависимости для системы мониторинга
Flask==2.3.3
Werkzeug==2.3.7
psutil==5.9.6
py-cpuinfo==9.0.0
"""
        
        try:
            with open(os.path.join(self.script_dir, "requirements.txt"), "w", encoding="utf-8") as f:
                f.write(requirements_content)
            self.print_status("Создан файл requirements.txt", "SUCCESS")
            return True
        except Exception as e:
            self.print_status(f"Ошибка создания requirements.txt: {e}", "WARNING")
            return False
    
    def create_run_script(self):
        """Создание скрипта запуска"""
        if self.is_windows:
            script_content = f'''@echo off
echo 🚀 Запуск системы мониторинга
echo =============================
"{self.python_exe}" simple_app.py
pause
'''
            script_name = "run_monitoring.bat"
        else:
            script_content = f'''#!/bin/bash
echo "🚀 Запуск системы мониторинга"
echo "============================="
"{self.python_exe}" simple_app.py
'''
            script_name = "run_monitoring.sh"
        
        script_path = os.path.join(self.script_dir, script_name)
        try:
            with open(script_path, 'w', encoding='utf-8') as f:
                f.write(script_content)
            
            if not self.is_windows:
                os.chmod(script_path, 0o755)
            
            self.print_status(f"Создан скрипт запуска: {script_name}", "SUCCESS")
            return True
        except Exception as e:
            self.print_status(f"Ошибка создания скрипта: {e}", "WARNING")
            return False
    
    def create_helper_files(self):
        """Создание всех вспомогательных файлов"""
        success = True
        
        # Создаем requirements.txt
        if not self.create_requirements_file():
            success = False
        
        # Создаем скрипт запуска
        if not self.create_run_script():
            success = False
            
        return success

    def run_application(self):
        """Запуск приложения"""
        simple_app_path = os.path.join(self.script_dir, "simple_app.py")
        
        if not os.path.exists(simple_app_path):
            self.print_status("Файл simple_app.py не найден!", "ERROR")
            return False
        
        self.print_status("Запуск приложения мониторинга...")
        print("\n" + "="*60)
        print("🚀 СИСТЕМА МОНИТОРИНГА ЗАПУЩЕНА")
        print("="*60)
        print("🌐 URL: http://127.0.0.1:5000")
        print("👤 Админка: http://127.0.0.1:5000/admin (admin/admin123)")
        print("🛑 Для остановки нажмите Ctrl+C")
        print("="*60)
        
        try:
            # Устанавливаем переменную окружения для виртуального окружения
            env = os.environ.copy()
            env['VIRTUAL_ENV'] = self.venv_path
            
            subprocess.run([self.python_exe, simple_app_path], 
                         cwd=self.script_dir, env=env)
            return True
        except KeyboardInterrupt:
            print("\n🛑 Приложение остановлено пользователем")
            return True
        except Exception as e:
            self.print_status(f"Ошибка запуска: {e}", "ERROR")
            return False
    
    def full_install_and_run(self):
        """Полная установка и запуск"""
        print("🚀 АВТОМАТИЧЕСКАЯ УСТАНОВКА СИСТЕМЫ МОНИТОРИНГА")
        print("=" * 55)
        
        steps = [
            ("Проверка Python", self.check_python_version),
            ("Создание виртуального окружения", self.create_venv),
            ("Обновление pip", self.upgrade_pip),
            ("Установка зависимостей", self.install_dependencies),
            ("Проверка установки", self.verify_installation),
            ("Создание вспомогательных файлов", self.create_helper_files),
        ]
        
        for step_name, step_func in steps:
            print(f"\n📋 {step_name}...")
            try:
                if not step_func():
                    self.print_status(f"Критическая ошибка на этапе: {step_name}", "ERROR")
                    return False
            except Exception as e:
                self.print_status(f"Исключение на этапе '{step_name}': {e}", "ERROR")
                return False
        
        print("\n" + "="*55)
        self.print_status("УСТАНОВКА ЗАВЕРШЕНА УСПЕШНО!", "SUCCESS")
        print("="*55)
        
        choice = input("\n🎯 Запустить приложение сейчас? (y/N): ").lower().strip()
        if choice in ['y', 'yes', 'да', 'д']:
            return self.run_application()
        else:
            print(f"\n📋 Для запуска позже используйте:")
            if self.is_windows:
                print(f"   run_monitoring.bat")
            else:
                print(f"   ./run_monitoring.sh")
            print(f"   или: {self.python_exe} simple_app.py")
            return True

def main():
    installer = AutoInstaller()
    
    try:
        success = installer.full_install_and_run()
        if not success:
            print("\n❌ Установка не завершена!")
            input("Нажмите Enter для выхода...")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Установка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n💥 Критическая ошибка: {e}")
        input("Нажмите Enter для выхода...")
        sys.exit(1)

if __name__ == "__main__":
    main()
