#!/usr/bin/env python3
"""
Точка входа в приложение мониторинга
"""
import os
import sys
import logging
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Добавляем корневую директорию в PYTHONPATH
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Настраиваем логирование
from app.utils.logger import configure_logging
configure_logging()

# Импортируем и запускаем приложение
from app import create_app
from app.utils.database import init_db
from app.services.monitoring.manager import MonitoringManager

def main():
    # Определяем режим работы
    env = os.environ.get("FLASK_ENV", "development")
    
    # Создаем приложение с соответствующей конфигурацией
    app = create_app(env)
    
    # Инициализируем базу данных
    with app.app_context():
        init_db()
    
    # Запускаем менеджер мониторинга
    monitoring_manager = MonitoringManager()
    monitoring_manager.start()
    
    # Получаем параметры запуска
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug = env == "development"
    
    # Запускаем приложение
    logging.info(f"Запуск приложения мониторинга на {host}:{port} в режиме {env}")
    app.run(host=host, port=port, debug=debug)

if __name__ == "__main__":
    main()
