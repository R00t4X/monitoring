import hashlib
import secrets
import os
from functools import wraps
from flask import session, request, abort
import logging

def generate_secret_key():
    """Генерация безопасного секретного ключа"""
    return secrets.token_hex(32)

def hash_password(password):
    """Хеширование пароля с солью"""
    salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return salt + pwdhash

def verify_password(stored_password, provided_password):
    """Проверка пароля"""
    salt = stored_password[:32]
    stored_hash = stored_password[32:]
    pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
    return pwdhash == stored_hash

def sanitize_log_message(message):
    """Очистка сообщения от чувствительных данных"""
    sensitive_patterns = [
        'password', 'passwd', 'pwd',
        'token', 'key', 'secret',
        'auth', 'credential', 'login'
    ]
    
    message_lower = message.lower()
    for pattern in sensitive_patterns:
        if pattern in message_lower:
            return "[SENSITIVE DATA FILTERED]"
    
    return message

def secure_headers(f):
    """Декоратор для добавления заголовков безопасности"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        response = f(*args, **kwargs)
        
        # Добавляем заголовки безопасности
        if hasattr(response, 'headers'):
            response.headers['X-Content-Type-Options'] = 'nosniff'
            response.headers['X-Frame-Options'] = 'DENY'
            response.headers['X-XSS-Protection'] = '1; mode=block'
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            response.headers['Content-Security-Policy'] = "default-src 'self'"
            
        return response
    return decorated_function

def rate_limit_check(max_requests=100, window_minutes=60):
    """Простая проверка лимита запросов"""
    client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)
    
    # В реальном приложении использовать Redis или базу данных
    # Это упрощенная версия
    
    return True  # Всегда разрешаем для демо

def log_security_event(event_type, details):
    """Логирование событий безопасности"""
    sanitized_details = sanitize_log_message(str(details))
    logging.warning(f"SECURITY EVENT - {event_type}: {sanitized_details}")
