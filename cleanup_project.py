#!/usr/bin/env python3
"""
Очистка проекта от неиспользуемых файлов.
"""
import os
import shutil
import glob

def remove_unused_files():
    """Удаление неиспользуемых файлов."""
    
    # Файлы для удаления
    files_to_remove = [
        'admin.py',  # Старый админ файл
        'advanced_monitor.py',  # Неиспользуемый продвинутый монитор
        'alert_system.py',  # Неиспользуемая система алертов
        'models.py',  # Старые модели
        'auto_setup.py',  # Старый скрипт установки
        'setup_and_run.py',  # Дублирующий скрипт
        'start.py',  # Неиспользуемый стартер
        'run.py',  # Неиспользуемый раннер (конфликтует с простой версией)
        'quick_start.py',  # Дублирует функциональность
        'check_sensitive.py',  # Утилита проверки (можно удалить после использования)
        'install.sh',  # Старый bash скрипт
        'install.bat',  # Старый batch скрипт
        'git_prepare.sh',  # Одноразовая утилита
        'install_and_run.sh',  # Дублирует функциональность
    ]
    
    # Директории для удаления
    dirs_to_remove = [
        'app/',  # Сложная структура, не используется в simple_app
        'config/',  # Конфигурация для сложной версии
        'migrations/',  # База данных не используется в простой версии
        'tests/',  # Тесты не созданы
        'scripts/',  # Дублирует функциональность корневых скриптов
        'static/uploads/',  # Не используется
        'templates/admin/',  # Админка реализована в simple_app
        'templates/auth/',  # Аутентификация упрощена
        'templates/errors/',  # Обработка ошибок встроена
    ]
    
    removed_files = []
    removed_dirs = []
    
    # Удаляем файлы
    for file_path in files_to_remove:
        if os.path.exists(file_path):
            os.remove(file_path)
            removed_files.append(file_path)
            print(f"🗑️ Удален файл: {file_path}")
    
    # Удаляем директории
    for dir_path in dirs_to_remove:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            removed_dirs.append(dir_path)
            print(f"🗑️ Удалена директория: {dir_path}")
    
    # Удаляем пустые директории
    empty_dirs = ['templates', 'static']
    for dir_path in empty_dirs:
        if os.path.exists(dir_path) and not os.listdir(dir_path):
            os.rmdir(dir_path)
            removed_dirs.append(dir_path)
            print(f"🗑️ Удалена пустая директория: {dir_path}")
    
    return removed_files, removed_dirs

def keep_essential_files():
    """Список файлов, которые нужно сохранить."""
    essential_files = [
        'simple_app.py',  # Основное приложение
        'system_monitor.py',  # Системный мониторинг
        'auto_setup_fixed.py',  # Рабочий скрипт установки
        'run_simple.py',  # Простой запуск
        'requirements_minimal.txt',  # Минимальные зависимости
        'requirements_compatible.txt',  # Совместимые зависимости
        '.gitignore',  # Исключения Git
        '.env.example',  # Пример конфигурации
        'README.md',  # Документация
        'cleanup.py',  # Утилита очистки
        'cleanup_project.py',  # Этот файл
    ]
    
    # Создаем базовые шаблоны если они нужны
    create_minimal_templates()
    
    return essential_files

def create_minimal_templates():
    """Создание минимальных шаблонов."""
    os.makedirs('templates', exist_ok=True)
    
    # Базовый шаблон
    base_template = '''<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Система Мониторинга{% endblock %}</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; }
        .header { background: #007bff; color: white; padding: 20px; margin: -20px -20px 20px -20px; border-radius: 8px 8px 0 0; }
        .nav { margin: 20px 0; }
        .nav a { margin-right: 15px; padding: 8px 16px; background: #007bff; color: white; text-decoration: none; border-radius: 4px; }
        .nav a:hover { background: #0056b3; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{% block header %}🖥️ Система Мониторинга{% endblock %}</h1>
        </div>
        <div class="nav">
            <a href="/">Главная</a>
            <a href="/servers">Серверы</a>
            <a href="/system">Система</a>
            <a href="/admin">Админка</a>
        </div>
        <main>
            {% block content %}{% endblock %}
        </main>
    </div>
</body>
</html>'''
    
    with open('templates/base.html', 'w', encoding='utf-8') as f:
        f.write(base_template)
    
    print("✅ Созданы минимальные шаблоны")

def main():
    """Основная функция очистки."""
    print("🧹 ОЧИСТКА ПРОЕКТА ОТ НЕИСПОЛЬЗУЕМЫХ ФАЙЛОВ")
    print("=" * 50)
    
    # Показываем что будет удалено
    print("\n📋 Файлы и директории для удаления:")
    
    choice = input("\n⚠️ Продолжить удаление? (y/N): ").lower().strip()
    if choice not in ['y', 'yes', 'да', 'д']:
        print("🛑 Очистка отменена")
        return
    
    removed_files, removed_dirs = remove_unused_files()
    essential_files = keep_essential_files()
    
    print(f"\n✅ Очистка завершена!")
    print(f"📄 Удалено файлов: {len(removed_files)}")
    print(f"📁 Удалено директорий: {len(removed_dirs)}")
    print(f"💾 Сохранено файлов: {len(essential_files)}")
    
    print("\n📋 Структура проекта после очистки:")
    for file in essential_files:
        if os.path.exists(file):
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} (не найден)")

if __name__ == "__main__":
    main()
