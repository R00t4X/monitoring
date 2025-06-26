"""
Основное веб-приложение системы мониторинга.
"""
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import os
import random
import socket
import sys
from datetime import datetime, timedelta
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring.log'),
        logging.StreamHandler()
    ]
)

# Безопасный импорт system_monitor
try:
    from core.system_monitor import system_monitor
    SYSTEM_MONITOR_AVAILABLE = True
    logging.info("System monitor загружен успешно")
except ImportError as e:
    logging.warning(f"System monitor недоступен: {e}")
    SYSTEM_MONITOR_AVAILABLE = False
    system_monitor = None

# Импортируем менеджер серверов
try:
    from data.server_manager import server_manager
    SERVER_MANAGER_AVAILABLE = True
except ImportError as e:
    SERVER_MANAGER_AVAILABLE = False
    logging.warning(f"Server manager недоступен: {e}")

# Импортируем менеджер базы данных
try:
    from data.database import db_manager
    DATABASE_AVAILABLE = True
    logging.info("База данных доступна")
except ImportError as e:
    DATABASE_AVAILABLE = False
    logging.warning(f"База данных недоступна: {e}")

# Импортируем SSH монитор
try:
    from monitoring.ssh_monitor import ssh_monitor
    SSH_MONITOR_AVAILABLE = True
    logging.info("SSH мониторинг доступен")
except ImportError as e:
    SSH_MONITOR_AVAILABLE = False
    logging.warning(f"SSH мониторинг недоступен: {e}")

# Создание экземпляра Flask приложения
app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Настройка Flask для правильной работы с UTF-8
app.config['JSON_AS_ASCII'] = False

# ...existing code...