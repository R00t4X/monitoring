#!/usr/bin/env python3
"""
Проверка проекта на наличие чувствительных данных перед коммитом
"""

import os
import re
import glob

class SensitiveDataChecker:
    def __init__(self):
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.issues = []
        
        # Паттерны для поиска чувствительных данных
        self.sensitive_patterns = {
            'passwords': [
                r'password\s*[=:]\s*["\']?[^"\'\s]{8,}',
                r'passwd\s*[=:]\s*["\']?[^"\'\s]{8,}',
                r'pwd\s*[=:]\s*["\']?[^"\'\s]{8,}'
            ],
            'api_keys': [
                r'api[_-]?key\s*[=:]\s*["\']?[a-zA-Z0-9]{20,}',
                r'secret[_-]?key\s*[=:]\s*["\']?[a-zA-Z0-9]{20,}',
                r'token\s*[=:]\s*["\']?[a-zA-Z0-9]{20,}'
            ],
            'database_urls': [
                r'mysql://[^"\'\s]+',
                r'postgresql://[^"\'\s]+',
                r'mongodb://[^"\'\s]+'
            ],
            'ip_addresses': [
                r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
            ]
        }
        
        # Файлы которые точно не должны быть в Git
        self.forbidden_files = [
            '*.log', '*.db', '*.sqlite', '*.sqlite3',
            '.env', '.env.local', '.env.production',
            'config.ini', 'secrets.json', 'credentials.json',
            '*.key', '*.pem', '*.p12'
        ]
        
        # Директории которые не должны быть в Git
        self.forbidden_dirs = [
            '__pycache__', '.vscode', '.idea', 
            'monitoring_venv', 'venv', 'env',
            'logs', 'backups', 'cache'
        ]
    
    def check_forbidden_files(self):
        """Проверка на наличие запрещенных файлов"""
        print("🔍 Проверка запрещенных файлов...")
        
        for pattern in self.forbidden_files:
            files = glob.glob(os.path.join(self.script_dir, "**/" + pattern), recursive=True)
            for file_path in files:
                rel_path = os.path.relpath(file_path, self.script_dir)
                self.issues.append(f"❌ Запрещенный файл: {rel_path}")
    
    def check_forbidden_dirs(self):
        """Проверка на наличие запрещенных директорий"""
        print("🔍 Проверка запрещенных директорий...")
        
        for root, dirs, files in os.walk(self.script_dir):
            for dir_name in dirs:
                if dir_name in self.forbidden_dirs:
                    dir_path = os.path.join(root, dir_name)
                    rel_path = os.path.relpath(dir_path, self.script_dir)
                    self.issues.append(f"❌ Запрещенная директория: {rel_path}")
    
    def check_file_contents(self):
        """Проверка содержимого файлов на чувствительные данные"""
        print("🔍 Проверка содержимого файлов...")
        
        # Проверяем только Python файлы и конфиги
        file_patterns = ['*.py', '*.json', '*.ini', '*.cfg', '*.conf', '*.yml', '*.yaml']
        
        for pattern in file_patterns:
            files = glob.glob(os.path.join(self.script_dir, "**/" + pattern), recursive=True)
            
            for file_path in files:
                # Пропускаем виртуальные окружения и другие исключения
                if any(excluded in file_path for excluded in ['/venv/', '/__pycache__/', '/.git/']):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        self._check_content_patterns(file_path, content)
                except Exception as e:
                    continue
    
    def _check_content_patterns(self, file_path, content):
        """Проверка содержимого файла на паттерны"""
        rel_path = os.path.relpath(file_path, self.script_dir)
        
        for category, patterns in self.sensitive_patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    for match in matches:
                        self.issues.append(f"⚠️  {category.upper()} в {rel_path}: {match[:50]}...")
    
    def check_gitignore(self):
        """Проверка наличия и корректности .gitignore"""
        print("🔍 Проверка .gitignore...")
        
        gitignore_path = os.path.join(self.script_dir, '.gitignore')
        
        if not os.path.exists(gitignore_path):
            self.issues.append("❌ Отсутствует файл .gitignore")
            return
        
        try:
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                gitignore_content = f.read()
            
            # Проверяем наличие основных паттернов
            required_patterns = [
                '__pycache__', '*.log', '.env', 'venv', '*.db'
            ]
            
            for pattern in required_patterns:
                if pattern not in gitignore_content:
                    self.issues.append(f"⚠️  .gitignore: отсутствует паттерн '{pattern}'")
                    
        except Exception as e:
            self.issues.append(f"❌ Ошибка чтения .gitignore: {e}")
    
    def run_check(self):
        """Запуск полной проверки"""
        print("🔒 ПРОВЕРКА НА ЧУВСТВИТЕЛЬНЫЕ ДАННЫЕ")
        print("="*40)
        
        self.check_gitignore()
        self.check_forbidden_files()
        self.check_forbidden_dirs()
        self.check_file_contents()
        
        print("\n📋 РЕЗУЛЬТАТЫ ПРОВЕРКИ:")
        print("="*40)
        
        if not self.issues:
            print("✅ Проблем не найдено! Проект готов для публикации.")
            return True
        else:
            print(f"❌ Найдено проблем: {len(self.issues)}")
            for issue in self.issues:
                print(f"   {issue}")
            
            print("\n🔧 РЕКОМЕНДАЦИИ:")
            print("1. Запустите cleanup.py для автоматической очистки")
            print("2. Проверьте и обновите .gitignore")
            print("3. Удалите или переместите чувствительные данные")
            print("4. Используйте переменные окружения для секретов")
            
            return False

def main():
    checker = SensitiveDataChecker()
    is_clean = checker.run_check()
    
    if not is_clean:
        exit(1)

if __name__ == "__main__":
    main()
