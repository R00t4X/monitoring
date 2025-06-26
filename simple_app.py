#!/usr/bin/env python3
"""
Упрощенная версия приложения мониторинга без сложных зависимостей.
"""
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import os
import random
import socket
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

# Создание экземпляра Flask приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Безопасный импорт system_monitor
try:
    from system_monitor import SystemMonitor
    system_monitor = SystemMonitor()
    SYSTEM_MONITOR_AVAILABLE = True
    logging.info("System monitor загружен успешно")
except ImportError as e:
    logging.warning(f"System monitor недоступен: {e}")
    SYSTEM_MONITOR_AVAILABLE = False
    system_monitor = None

# Данные серверов (упрощенная версия)
servers_data = [
    {
        'id': 1,
        'name': 'Web-сервер 1',
        'ip': '192.168.1.10',
        'port': 80,
        'status': 'online',
        'cpu': 45,
        'memory': 67,
        'disk': 32,
        'network_in': 1250,
        'network_out': 890,
        'uptime': '15 дней 8 часов',
        'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'location': 'Москва, РФ',
        'os': 'Ubuntu 22.04',
        'alerts': []
    }
]

# Данные пользователей
ADMIN_CREDENTIALS = {
    'username': os.environ.get('ADMIN_USERNAME', 'admin'),
    'password': os.environ.get('ADMIN_PASSWORD', 'admin123')
}

def get_local_server_data():
    """Получение данных о локальной машине"""
    if not SYSTEM_MONITOR_AVAILABLE:
        return {
            'id': 0,
            'name': 'Локальная машина (базовые данные)',
            'ip': '127.0.0.1',
            'port': 5000,
            'status': 'online',
            'cpu': random.randint(10, 50),
            'memory': random.randint(30, 70),
            'disk': random.randint(20, 60),
            'network_in': random.randint(100, 1000),
            'network_out': random.randint(50, 500),
            'uptime': 'Неизвестно',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'location': 'Локальная машина',
            'os': 'Система мониторинга',
            'alerts': []
        }
    
    try:
        metrics = system_monitor.get_all_metrics()
        system_info = metrics.get('system_info', {})
        cpu_data = metrics.get('cpu', {})
        memory_data = metrics.get('memory', {})
        disk_data = metrics.get('disk', {})
        network_data = metrics.get('network', {})
        
        # Основной диск
        main_disk_percent = 0
        if disk_data.get('partitions'):
            main_disk_percent = disk_data['partitions'][0].get('percent', 0)
        
        return {
            'id': 0,
            'name': f'Локальная машина ({system_info.get("hostname", "Unknown")})',
            'ip': socket.gethostbyname(socket.gethostname()),
            'port': 5000,
            'status': 'online',
            'cpu': cpu_data.get('cpu_percent', 0),
            'memory': memory_data.get('percent', 0),
            'disk': main_disk_percent,
            'network_in': network_data.get('speed', {}).get('bytes_recv_per_sec', 0),
            'network_out': network_data.get('speed', {}).get('bytes_sent_per_sec', 0),
            'uptime': system_info.get('uptime', 'Неизвестно'),
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'location': 'Локальная машина',
            'os': f"{system_info.get('platform', 'Unknown')}",
            'alerts': []
        }
    except Exception as e:
        logging.error(f"Ошибка получения данных локальной машины: {e}")
        return None

def update_servers_list():
    """Обновление списка серверов с локальной машиной"""
    global servers_data
    local_server = get_local_server_data()
    if local_server:
        # Удаляем старую запись локального сервера если есть
        servers_data = [s for s in servers_data if s['id'] != 0]
        # Добавляем обновленную запись в начало
        servers_data.insert(0, local_server)

@app.route('/')
def index():
    """Главная страница"""
    update_servers_list()
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'message': 'Приложение работает',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'system_monitor': SYSTEM_MONITOR_AVAILABLE
    })

@app.route('/api/status')
def status():
    """Status endpoint для мониторинга"""
    return jsonify({
        'application': 'monitoring',
        'version': '1.0.0',
        'status': 'active',
        'features': {
            'system_monitor': SYSTEM_MONITOR_AVAILABLE,
            'servers_count': len(servers_data)
        }
    })

@app.route('/servers')
def servers():
    """Страница списка серверов"""
    update_servers_list()
    return render_template('servers.html', servers=servers_data)

@app.route('/system')
def system_status():
    """Страница детального мониторинга локальной системы"""
    if not SYSTEM_MONITOR_AVAILABLE:
        return render_template('system_unavailable.html')
    
    try:
        report = system_monitor.get_all_metrics()
        return render_template('system_status.html', report=report)
    except Exception as e:
        logging.error(f"Ошибка получения системных метрик: {e}")
        return render_template('system_unavailable.html', error=str(e))

@app.route('/api/system')
def api_system():
    """API для получения данных системы"""
    if not SYSTEM_MONITOR_AVAILABLE:
        return jsonify({'error': 'System monitor unavailable'})
    
    try:
        return jsonify(system_monitor.get_all_metrics())
    except Exception as e:
        return jsonify({'error': str(e)})

@app.route('/api/servers/update')
def api_servers_update():
    """API для получения обновленных данных серверов"""
    update_servers_list()
    return jsonify({
        'servers': servers_data,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/admin')
def admin():
    """Страница входа в админку"""
    if 'admin_logged_in' in session:
        return render_template('admin_dashboard.html', servers=servers_data)
    return render_template('admin_login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Обработка входа в админку"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_CREDENTIALS['username'] and password == ADMIN_CREDENTIALS['password']:
        session['admin_logged_in'] = True
        flash('Успешный вход в админку!', 'success')
        logging.info(f"Admin login: {username}")
        return redirect(url_for('admin'))
    else:
        flash('Неверный логин или пароль!', 'error')
        logging.warning(f"Failed admin login attempt: {username}")
        return redirect(url_for('admin'))

@app.route('/admin/logout')
def admin_logout():
    """Выход из админки"""
    session.pop('admin_logged_in', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('index'))

# Замена deprecated @app.before_first_request на современный подход
app_initialized = False

@app.before_request
def initialize_app():
    """Инициализация приложения при первом запросе"""
    global app_initialized
    if not app_initialized:
        app_initialized = True
        # Инициализируем список серверов с локальной машиной
        update_servers_list()
        logging.info("Приложение инициализировано")

# Обработчики ошибок
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Страница не найдена'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    logging.info("Запуск упрощенного приложения мониторинга")
    
    # Получаем параметры запуска
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    print(f"🚀 Запуск приложения мониторинга на {host}:{port}")
    print(f"🌐 Откройте браузер: http://{host}:{port}")
    
    app.run(host=host, port=port, debug=debug)
