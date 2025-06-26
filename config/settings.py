"""
Конфигурационные параметры приложения.
"""
import os
import secrets
from datetime import timedelta

class BaseConfig:
    """Базовая конфигурация."""
    # Безопасность
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    SESSION_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_HTTPONLY = True
    
    # База данных
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Мониторинг
    MONITORING_INTERVAL = int(os.environ.get('MONITORING_INTERVAL', 30))
    
    # Пороги оповещений
    ALERT_CPU_THRESHOLD = float(os.environ.get('ALERT_CPU_THRESHOLD', 80.0))
    ALERT_MEMORY_THRESHOLD = float(os.environ.get('ALERT_MEMORY_THRESHOLD', 85.0))
    ALERT_DISK_THRESHOLD = float(os.environ.get('ALERT_DISK_THRESHOLD', 90.0))
    
    # Логирование
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'logs')
    LOG_FILENAME = 'monitoring.log'
    
    # Пути к директориям
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    TEMPLATES_DIR = os.path.join(BASE_DIR, 'templates')
    STATIC_DIR = os.path.join(BASE_DIR, 'static')

class DevelopmentConfig(BaseConfig):
    """Конфигурация для разработки."""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BaseConfig.BASE_DIR, 'data-dev.sqlite')
    
    # Дополнительные настройки для разработки
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0

class TestingConfig(BaseConfig):
    """Конфигурация для тестирования."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(BaseConfig.BASE_DIR, 'data-test.sqlite')
    WTF_CSRF_ENABLED = False

class ProductionConfig(BaseConfig):
    """Конфигурация для продакшена."""
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(BaseConfig.BASE_DIR, 'data.sqlite')
    
    # Дополнительные настройки безопасности
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    PREFERRED_URL_SCHEME = 'https'

# Словарь доступных конфигураций
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
