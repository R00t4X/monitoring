#!/usr/bin/env python3
"""
Исправленная автонастройка с поэтапной установкой зависимостей.
"""
import subprocess
import sys
import os
import venv
import platform

class FixedAutoSetup:
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
    
    def install_minimal_requirements(self):
        """Установка минимальных зависимостей"""
        self.print_step("Установка минимальных зависимостей...")
        
        # Сначала устанавливаем основные пакеты
        basic_packages = [
            "Flask==2.3.3",
            "Werkzeug==2.3.7"
        ]
        
        for package in basic_packages:
            try:
                subprocess.run([
                    self.pip_exe, "install", package
                ], check=True, capture_output=True, text=True)
                self.print_success(f"Установлен {package}")
            except subprocess.CalledProcessError as e:
                self.print_error(f"Ошибка установки {package}: {e}")
                return False
        
        # Затем устанавливаем системные мониторинг пакеты
        system_packages = [
            "psutil==5.9.6",
            "py-cpuinfo==9.0.0"
        ]
        
        for package in system_packages:
            try:
                subprocess.run([
                    self.pip_exe, "install", package
                ], check=True, capture_output=True, text=True)
                self.print_success(f"Установлен {package}")
            except subprocess.CalledProcessError as e:
                self.print_warning(f"Не удалось установить {package}: {e}")
                # Продолжаем работу без этого пакета
        
        return True
    
    def install_optional_requirements(self):
        """Установка дополнительных зависимостей"""
        self.print_step("Установка дополнительных зависимостей...")
        
        optional_packages = [
            "Flask-SocketIO==5.3.6",
            "Flask-SQLAlchemy==3.1.1",
            "numpy==1.25.2"
        ]
        
        installed_count = 0
        for package in optional_packages:
            try:
                subprocess.run([
                    self.pip_exe, "install", package
                ], check=True, capture_output=True, text=True, timeout=120)
                self.print_success(f"Установлен {package}")
                installed_count += 1
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
                self.print_warning(f"Не удалось установить {package}: {e}")
        
        self.print_success(f"Установлено {installed_count} из {len(optional_packages)} дополнительных пакетов")
        return True
    
    def check_imports(self):
        """Проверка импортов"""
        self.print_step("Проверка основных импортов...")
        
        test_script = '''
import sys
try:
    import flask
    print("✅ Flask: OK")
except ImportError as e:
    print(f"❌ Flask: {e}")
    sys.exit(1)

try:
    import psutil
    print("✅ psutil: OK")
except ImportError:
    print("⚠️ psutil: Not available")

try:
    import cpuinfo
    print("✅ cpuinfo: OK")
except ImportError:
    print("⚠️ cpuinfo: Not available")

print("SUCCESS: Basic modules available")
'''
        
        try:
            result = subprocess.run([
                self.python_exe, "-c", test_script
            ], capture_output=True, text=True, check=True)
            
            print(result.stdout)
            if "SUCCESS" in result.stdout:
                self.print_success("Основные модули доступны")
                return True
            else:
                self.print_error("Не все основные модули доступны")
                return False
                
        except subprocess.CalledProcessError as e:
            self.print_error(f"Ошибка проверки модулей: {e}")
            return False
    
    def create_startup_script(self):
        """Создание скрипта запуска"""
        self.print_step("Создание скрипта запуска...")
        
        if self.is_windows:
            script_content = f'''@echo off
echo 🚀 Запуск системы мониторинга
echo ==============================
"{self.python_exe}" simple_app.py
pause
'''
            script_name = "start_monitoring.bat"
        else:
            script_content = f'''#!/bin/bash
echo "🚀 Запуск системы мониторинга"
echo "=============================="
"{self.python_exe}" simple_app.py
'''
            script_name = "start_monitoring.sh"
        
        script_path = os.path.join(self.script_dir, script_name)
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        if not self.is_windows:
            os.chmod(script_path, 0o755)
        
        self.print_success(f"Создан скрипт запуска: {script_name}")
        return True
    
    def run_app(self):
        """Запуск приложения"""
        self.print_step("Запуск приложения...")
        
        # Проверяем наличие simple_app.py
        simple_app_path = os.path.join(self.script_dir, "simple_app.py")
        if not os.path.exists(simple_app_path):
            self.print_error("Файл simple_app.py не найден!")
            return False
        
        print("\n" + "="*60)
        print("🚀 ЗАПУСК ПРИЛОЖЕНИЯ МОНИТОРИНГА")
        print("="*60)
        print("🌐 Откройте браузер: http://127.0.0.1:5000")
        print("🛑 Для остановки нажмите Ctrl+C")
        print("="*60)
        
        try:
            subprocess.run([self.python_exe, simple_app_path], cwd=self.script_dir)
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
        print("🚀 ИСПРАВЛЕННАЯ АВТОНАСТРОЙКА СИСТЕМЫ МОНИТОРИНГА")
        print("="*60)
        
        steps = [
            ("Создание виртуального окружения", self.create_venv),
            ("Обновление pip", self.upgrade_pip),
            ("Установка основных зависимостей", self.install_minimal_requirements),
            ("Установка дополнительных зависимостей", self.install_optional_requirements),
            ("Проверка модулей", self.check_imports),
            ("Создание скрипта запуска", self.create_startup_script),
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
        
        choice = input("\nЗапустить приложение сейчас? (y/N): ").lower().strip()
        if choice in ['y', 'yes', 'да', 'д']:
            return self.run_app()
        else:
            print("\n📝 Для запуска позже используйте:")
            if self.is_windows:
                print("   start_monitoring.bat")
            else:
                print("   ./start_monitoring.sh")
            print("   или")
            print(f"   {self.python_exe} simple_app.py")
            return True

def main():
    setup = FixedAutoSetup()
    
    try:
        success = setup.setup_and_run()
        if not success:
            print("\n❌ Установка не завершена!")
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n🛑 Установка прервана пользователем")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
