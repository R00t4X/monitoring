"""
Автоматическая установка всех зависимостей и запуск приложения.
"""
import subprocess
import sys
import os
import venv
import platform

class AutoInstaller:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.venv_name = "monitoring_venv"
        self.venv_path = os.path.join(self.script_dir, self.venv_name)
        self.is_windows = platform.system() == "Windows"
        
        if self.is_windows:
            self.python_exe = os.path.join(self.venv_path, "Scripts", "python.exe")
            self.pip_exe = os.path.join(self.venv_path, "Scripts", "pip.exe")
        else:
            self.python_exe = os.path.join(self.venv_path, "bin", "python")
            self.pip_exe = os.path.join(self.venv_path, "bin", "pip")
    
    # ...existing code...

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
