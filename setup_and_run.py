import subprocess
import sys
import os
import venv
import platform

# Настройки
VENV_DIR = "monitoring_venv"
REQUIREMENTS = [
    "Flask==2.3.3",
    "Werkzeug==2.3.7", 
    "psutil==5.9.6",
    "py-cpuinfo==9.0.0"
]

class MonitoringSetup:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.venv_path = os.path.join(self.script_dir, VENV_DIR)
        self.is_windows = platform.system() == "Windows"
        
        # Пути для активации виртуальной среды
        if self.is_windows:
            self.venv_python = os.path.join(self.venv_path, "Scripts", "python.exe")
            self.venv_pip = os.path.join(self.venv_path, "Scripts", "pip.exe")
            self.activate_script = os.path.join(self.venv_path, "Scripts", "activate.bat")
        else:
            self.venv_python = os.path.join(self.venv_path, "bin", "python")
            self.venv_pip = os.path.join(self.venv_path, "bin", "pip")
            self.activate_script = os.path.join(self.venv_path, "bin", "activate")

    def print_banner(self):
        """Отображение баннера приложения"""
        print("=" * 70)
        print("🚀 АВТОУСТАНОВКА СИСТЕМЫ МОНИТОРИНГА")
        print("=" * 70)
        print("🔧 Автоматическая настройка виртуальной среды")
        print("📦 Установка всех необходимых зависимостей")
        print("🖥️  Запуск приложения мониторинга")
        print("=" * 70)
        print()

    def check_python_version(self):
        """Проверка версии Python"""
        print("🔍 Проверка версии Python...")
        version = sys.version_info
        
        if version.major < 3 or (version.major == 3 and version.minor < 7):
            print("❌ Требуется Python 3.7 или выше!")
            print(f"   Текущая версия: {version.major}.{version.minor}.{version.micro}")
            return False
        
        print(f"✅ Python {version.major}.{version.minor}.{version.micro} - подходит!")
        return True

    def create_virtual_environment(self):
        """Создание виртуальной среды"""
        print("🏗️  Создание виртуальной среды...")
        
        if os.path.exists(self.venv_path):
            print(f"📁 Виртуальная среда уже существует: {VENV_DIR}")
            return True
        
        try:
            print(f"📁 Создаем виртуальную среду в: {VENV_DIR}")
            venv.create(self.venv_path, with_pip=True)
            print("✅ Виртуальная среда успешно создана!")
            return True
        except Exception as e:
            print(f"❌ Ошибка создания виртуальной среды: {e}")
            return False

    def upgrade_pip(self):
        """Обновление pip в виртуальной среде"""
        print("📈 Обновление pip...")
        try:
            subprocess.check_call([
                self.venv_python, "-m", "pip", "install", "--upgrade", "pip"
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print("✅ pip успешно обновлен!")
            return True
        except subprocess.CalledProcessError as e:
            print(f"⚠️  Предупреждение: не удалось обновить pip: {e}")
            return True  # Продолжаем даже если pip не обновился

    def install_dependencies(self):
        """Установка зависимостей"""
        print("📦 Установка зависимостей...")
        
        # Проверяем наличие requirements.txt
        requirements_file = os.path.join(self.script_dir, "requirements.txt")
        
        if os.path.exists(requirements_file):
            print("📋 Найден файл requirements.txt, устанавливаем из него...")
            try:
                subprocess.check_call([
                    self.venv_pip, "install", "-r", requirements_file
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print("✅ Зависимости из requirements.txt установлены!")
                return True
            except subprocess.CalledProcessError as e:
                print(f"⚠️  Ошибка установки из requirements.txt: {e}")
                print("🔄 Попробуем установить зависимости вручную...")
        
        # Установка зависимостей по одной
        print("📦 Установка базовых зависимостей...")
        for package in REQUIREMENTS:
            try:
                print(f"   📥 Устанавливаем {package}...")
                subprocess.check_call([
                    self.venv_pip, "install", package
                ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                print(f"   ✅ {package} установлен!")
            except subprocess.CalledProcessError as e:
                print(f"   ❌ Ошибка установки {package}: {e}")
                return False
        
        print("✅ Все зависимости успешно установлены!")
        return True

    def create_requirements_file(self):
        """Создание файла requirements.txt если его нет"""
        requirements_file = os.path.join(self.script_dir, "requirements.txt")
        
        if not os.path.exists(requirements_file):
            print("📝 Создаем файл requirements.txt...")
            try:
                with open(requirements_file, 'w', encoding='utf-8') as f:
                    f.write("# Зависимости для системы мониторинга\n")
                    for package in REQUIREMENTS:
                        f.write(f"{package}\n")
                print("✅ Файл requirements.txt создан!")
            except Exception as e:
                print(f"⚠️  Не удалось создать requirements.txt: {e}")

    def check_app_files(self):
        """Проверка наличия необходимых файлов приложения"""
        print("📋 Проверка файлов приложения...")
        
        required_files = ["app.py", "system_monitor.py"]
        missing_files = []
        
        for file in required_files:
            file_path = os.path.join(self.script_dir, file)
            if not os.path.exists(file_path):
                missing_files.append(file)
        
        if missing_files:
            print(f"❌ Отсутствуют файлы: {', '.join(missing_files)}")
            return False
        
        print("✅ Все необходимые файлы найдены!")
        return True

    def create_directories(self):
        """Создание необходимых директорий"""
        print("📁 Создание директорий...")
        
        directories = ["templates", "static"]
        
        for directory in directories:
            dir_path = os.path.join(self.script_dir, directory)
            if not os.path.exists(dir_path):
                try:
                    os.makedirs(dir_path)
                    print(f"✅ Создана директория: {directory}")
                except Exception as e:
                    print(f"⚠️  Не удалось создать директорию {directory}: {e}")

    def run_application(self):
        """Запуск приложения"""
        print("🚀 Запуск приложения мониторинга...")
        print("=" * 70)
        print("🌐 Приложение будет доступно по адресу: http://127.0.0.1:5000")
        print("🛑 Для остановки нажмите Ctrl+C")
        print("=" * 70)
        print()
        
        app_path = os.path.join(self.script_dir, "app.py")
        
        try:
            # Запуск приложения в виртуальной среде
            env = os.environ.copy()
            env['PYTHONPATH'] = self.script_dir
            
            subprocess.run([self.venv_python, app_path], 
                         cwd=self.script_dir, 
                         env=env)
        except KeyboardInterrupt:
            print("\n🛑 Приложение остановлено пользователем")
        except Exception as e:
            print(f"❌ Ошибка запуска приложения: {e}")

    def show_manual_instructions(self):
        """Показать инструкции для ручного запуска"""
        print("\n" + "=" * 70)
        print("📋 ИНСТРУКЦИИ ДЛЯ РУЧНОГО ЗАПУСКА:")
        print("=" * 70)
        
        if self.is_windows:
            print(f"1. Активация виртуальной среды:")
            print(f"   {self.activate_script}")
            print(f"2. Запуск приложения:")
            print(f"   python app.py")
        else:
            print(f"1. Активация виртуальной среды:")
            print(f"   source {self.activate_script}")
            print(f"2. Запуск приложения:")
            print(f"   python app.py")
        
        print("\n3. Открыть в браузере: http://127.0.0.1:5000")
        print("=" * 70)

    def setup_and_run(self):
        """Основная функция установки и запуска"""
        self.print_banner()
        
        # Проверка версии Python
        if not self.check_python_version():
            return False
        
        # Создание виртуальной среды
        if not self.create_virtual_environment():
            return False
        
        # Обновление pip
        if not self.upgrade_pip():
            return False
        
        # Создание файла requirements.txt
        self.create_requirements_file()
        
        # Установка зависимостей
        if not self.install_dependencies():
            return False
        
        # Создание директорий
        self.create_directories()
        
        # Проверка файлов приложения
        if not self.check_app_files():
            print("❌ Не все файлы приложения найдены!")
            print("📁 Убедитесь, что файлы app.py и system_monitor.py находятся в той же папке")
            return False
        
        print("\n✅ Настройка завершена успешно!")
        print("🎉 Запускаем приложение...")
        print()
        
        # Запуск приложения
        self.run_application()
        
        # Показать инструкции для ручного запуска
        self.show_manual_instructions()
        
        return True

def main():
    """Главная функция"""
    setup = MonitoringSetup()
    
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
