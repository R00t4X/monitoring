import os
from datetime import timedelta

class Config:
    """Базовая конфигурация"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Настройки безопасности
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = timedelta(hours=2)
    
    # Настройки мониторинга
    MONITORING_INTERVAL = int(os.environ.get('MONITORING_INTERVAL', 30))
    MAX_SERVERS = int(os.environ.get('MAX_SERVERS', 50))
    
    # Пороги алертов
    ALERT_CPU_THRESHOLD = int(os.environ.get('ALERT_CPU_THRESHOLD', 80))
    ALERT_MEMORY_THRESHOLD = int(os.environ.get('ALERT_MEMORY_THRESHOLD', 85))
    ALERT_DISK_THRESHOLD = int(os.environ.get('ALERT_DISK_THRESHOLD', 90))
    
    # Админ учетные данные
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')
    
    # Настройки логирования
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'monitoring.log')
    
class DevelopmentConfig(Config):
    """Конфигурация разработки"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """Конфигурация продакшена"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """Конфигурация тестирования"""
    TESTING = True
    LOG_LEVEL = 'CRITICAL'

# Выбор конфигурации по переменной окружения
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
