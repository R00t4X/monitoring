#!/usr/bin/env python3
"""
Скрипт для очистки проекта от ненужных файлов перед публикацией
"""

import os
import shutil
import glob
import sys

def print_step(message):
    print(f"🧹 {message}")

def print_success(message):
    print(f"✅ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def print_error(message):
    print(f"❌ {message}")

class ProjectCleaner:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.removed_files = []
        self.removed_dirs = []
        
    def clean_python_cache(self):
        """Удаление Python кеша"""
        print_step("Удаление Python кеша...")
        
        # Поиск __pycache__ директорий
        for root, dirs, files in os.walk(self.script_dir):
            for dir_name in dirs[:]:
                if dir_name == '__pycache__':
                    cache_path = os.path.join(root, dir_name)
                    try:
                        shutil.rmtree(cache_path)
                        self.removed_dirs.append(cache_path)
                        dirs.remove(dir_name)
                    except Exception as e:
                        print_error(f"Не удалось удалить {cache_path}: {e}")
        
        # Удаление .pyc файлов
        pyc_files = glob.glob(os.path.join(self.script_dir, "**/*.pyc"), recursive=True)
        for file_path in pyc_files:
            try:
                os.remove(file_path)
                self.removed_files.append(file_path)
            except Exception as e:
                print_error(f"Не удалось удалить {file_path}: {e}")
    
    def clean_virtual_environments(self):
        """Удаление виртуальных окружений"""
        print_step("Удаление виртуальных окружений...")
        
        venv_names = ['monitoring_venv', 'venv', 'env', '.venv']
        
        for venv_name in venv_names:
            venv_path = os.path.join(self.script_dir, venv_name)
            if os.path.exists(venv_path):
                try:
                    shutil.rmtree(venv_path)
                    self.removed_dirs.append(venv_path)
                    print_success(f"Удалено виртуальное окружение: {venv_name}")
                except Exception as e:
                    print_error(f"Не удалось удалить {venv_path}: {e}")
    
    def clean_logs(self):
        """Удаление логов"""
        print_step("Удаление файлов логов...")
        
        log_patterns = ['*.log', 'logs/*', 'log/*']
        
        for pattern in log_patterns:
            files = glob.glob(os.path.join(self.script_dir, pattern), recursive=True)
            for file_path in files:
                try:
                    if os.path.isfile(file_path):
                        os.remove(file_path)
                        self.removed_files.append(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                        self.removed_dirs.append(file_path)
                except Exception as e:
                    print_error(f"Не удалось удалить {file_path}: {e}")
    
    def clean_temp_files(self):
        """Удаление временных файлов"""
        print_step("Удаление временных файлов...")
        
        temp_patterns = ['*.tmp', '*.temp', '*~', '.DS_Store', 'Thumbs.db']
        
        for pattern in temp_patterns:
            files = glob.glob(os.path.join(self.script_dir, "**/" + pattern), recursive=True)
            for file_path in files:
                try:
                    os.remove(file_path)
                    self.removed_files.append(file_path)
                except Exception as e:
                    print_error(f"Не удалось удалить {file_path}: {e}")
    
    def clean_databases(self):
        """Удаление файлов баз данных"""
        print_step("Удаление файлов баз данных...")
        
        db_patterns = ['*.db', '*.sqlite', '*.sqlite3']
        
        for pattern in db_patterns:
            files = glob.glob(os.path.join(self.script_dir, "**/" + pattern), recursive=True)
            for file_path in files:
                try:
                    os.remove(file_path)
                    self.removed_files.append(file_path)
                    print_success(f"Удален файл БД: {os.path.basename(file_path)}")
                except Exception as e:
                    print_error(f"Не удалось удалить {file_path}: {e}")
    
    def clean_backups(self):
        """Удаление резервных копий"""
        print_step("Удаление резервных копий...")
        
        backup_patterns = ['backup_*.json', '*.backup', '*.bak']
        
        for pattern in backup_patterns:
            files = glob.glob(os.path.join(self.script_dir, pattern))
            for file_path in files:
                try:
                    os.remove(file_path)
                    self.removed_files.append(file_path)
                    print_success(f"Удален бэкап: {os.path.basename(file_path)}")
                except Exception as e:
                    print_error(f"Не удалось удалить {file_path}: {e}")
    
    def clean_ide_files(self):
        """Удаление файлов IDE"""
        print_step("Удаление файлов IDE...")
        
        ide_dirs = ['.vscode', '.idea', '.settings']
        ide_files = ['*.swp', '*.swo', '.project', '.pydevproject']
        
        # Удаление директорий IDE
        for ide_dir in ide_dirs:
            dir_path = os.path.join(self.script_dir, ide_dir)
            if os.path.exists(dir_path):
                try:
                    shutil.rmtree(dir_path)
                    self.removed_dirs.append(dir_path)
                    print_success(f"Удалена директория IDE: {ide_dir}")
                except Exception as e:
                    print_error(f"Не удалось удалить {dir_path}: {e}")
        
        # Удаление файлов IDE
        for pattern in ide_files:
            files = glob.glob(os.path.join(self.script_dir, "**/" + pattern), recursive=True)
            for file_path in files:
                try:
                    os.remove(file_path)
                    self.removed_files.append(file_path)
                except Exception as e:
                    print_error(f"Не удалось удалить {file_path}: {e}")
    
    def clean_sensitive_files(self):
        """Удаление чувствительных файлов"""
        print_step("Удаление чувствительных файлов...")
        
        sensitive_patterns = ['.env*', 'config.ini', 'secrets.json', 'credentials.json', '*.key', '*.pem']
        
        for pattern in sensitive_patterns:
            files = glob.glob(os.path.join(self.script_dir, pattern))
            for file_path in files:
                if not file_path.endswith('.example'):  # Сохраняем примеры
                    try:
                        os.remove(file_path)
                        self.removed_files.append(file_path)
                        print_warning(f"Удален чувствительный файл: {os.path.basename(file_path)}")
                    except Exception as e:
                        print_error(f"Не удалось удалить {file_path}: {e}")
    
    def show_summary(self):
        """Показать сводку удаленных файлов"""
        print("\n" + "="*60)
        print("📋 СВОДКА ОЧИСТКИ")
        print("="*60)
        
        print(f"📁 Удалено директорий: {len(self.removed_dirs)}")
        for dir_path in self.removed_dirs:
            print(f"   - {os.path.relpath(dir_path, self.script_dir)}")
        
        print(f"\n📄 Удалено файлов: {len(self.removed_files)}")
        for file_path in self.removed_files:
            print(f"   - {os.path.relpath(file_path, self.script_dir)}")
        
        if not self.removed_files and not self.removed_dirs:
            print_success("Проект уже чистый! 🧹")
        else:
            print_success(f"Очистка завершена! Освобождено место от {len(self.removed_files + self.removed_dirs)} элементов")
    
    def run_cleanup(self):
        """Запуск полной очистки"""
        print("🧹 ОЧИСТКА ПРОЕКТА ДЛЯ GITHUB")
        print("="*40)
        
        cleanup_steps = [
            self.clean_python_cache,
            self.clean_virtual_environments,
            self.clean_logs,
            self.clean_temp_files,
            self.clean_databases,
            self.clean_backups,
            self.clean_ide_files,
            self.clean_sensitive_files
        ]
        
        for step in cleanup_steps:
            try:
                step()
            except Exception as e:
                print_error(f"Ошибка в этапе очистки: {e}")
        
        self.show_summary()

def main():
    cleaner = ProjectCleaner()
    
    print("⚠️  ВНИМАНИЕ: Этот скрипт удалит файлы, которые не должны быть в Git!")
    print("Файлы для удаления:")
    print("- Python кеш (__pycache__/)")
    print("- Виртуальные окружения")
    print("- Логи (*.log)")
    print("- Временные файлы")
    print("- Базы данных")
    print("- Резервные копии")
    print("- Файлы IDE")
    print("- Чувствительные файлы (.env, ключи)")
    
    try:
        choice = input("\nПродолжить? (y/N): ").lower().strip()
        if choice in ['y', 'yes', 'да', 'д']:
            cleaner.run_cleanup()
        else:
            print("🛑 Очистка отменена")
    except KeyboardInterrupt:
        print("\n🛑 Очистка прервана пользователем")

if __name__ == "__main__":
    main()
