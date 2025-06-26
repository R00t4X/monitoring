from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import os
from datetime import datetime, timedelta
import random
import logging
from functools import wraps

# Безопасный импорт system_monitor
try:
    from system_monitor import system_monitor
    SYSTEM_MONITOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Предупреждение: system_monitor недоступен - {e}")
    SYSTEM_MONITOR_AVAILABLE = False
    system_monitor = None

import socket

# Настройка безопасного логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring.log'),
        logging.StreamHandler()
    ]
)

# Фильтр для исключения чувствительных данных из логов
class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        # Убираем чувствительные данные из логов
        sensitive_keywords = ['password', 'token', 'secret', 'key', 'auth']
        message = record.getMessage().lower()
        
        for keyword in sensitive_keywords:
            if keyword in message:
                record.msg = "Sensitive data filtered from logs"
                record.args = ()
                break
        
        return True

# Применяем фильтр ко всем логгерам
for handler in logging.getLogger().handlers:
    handler.addFilter(SensitiveDataFilter())

# Создание экземпляра Flask приложения
app = Flask(__name__)

# Базовая конфигурация
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# Учетные данные администратора
ADMIN_CREDENTIALS = {
    'username': os.environ.get('ADMIN_USERNAME', 'admin'),
    'password': os.environ.get('ADMIN_PASSWORD', 'admin123')
}

# Простая база данных серверов (в реальном приложении используйте настоящую БД)
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
    },
    {
        'id': 2,
        'name': 'База данных',
        'ip': '192.168.1.20',
        'port': 3306,
        'status': 'online',
        'cpu': 78,
        'memory': 89,
        'disk': 45,
        'network_in': 2340,
        'network_out': 1560,
        'uptime': '30 дней 12 часов',
        'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'location': 'СПб, РФ',
        'os': 'CentOS 8',
        'alerts': ['Высокое использование CPU', 'Высокое использование памяти']
    },
    {
        'id': 3,
        'name': 'Файловый сервер',
        'ip': '192.168.1.30',
        'port': 21,
        'status': 'warning',
        'cpu': 15,
        'memory': 45,
        'disk': 92,
        'network_in': 450,
        'network_out': 320,
        'uptime': '5 дней 3 часа',
        'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'location': 'Екатеринбург, РФ',
        'os': 'Windows Server 2019',
        'alerts': ['Критически мало места на диске']
    },
    {
        'id': 4,
        'name': 'Backup сервер',
        'ip': '192.168.1.40',
        'port': 22,
        'status': 'offline',
        'cpu': 0,
        'memory': 0,
        'disk': 0,
        'network_in': 0,
        'network_out': 0,
        'uptime': '0 дней 0 часов',
        'last_check': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
        'location': 'Новосибирск, РФ',
        'os': 'Debian 11',
        'alerts': ['Сервер недоступен']
    }
]

# Система уведомлений
notifications = [
    {
        'id': 1,
        'type': 'warning',
        'message': 'Файловый сервер: критически мало места на диске (92%)',
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'server_id': 3
    },
    {
        'id': 2,
        'type': 'error',
        'message': 'Backup сервер недоступен уже 2 часа',
        'timestamp': (datetime.now() - timedelta(hours=2)).strftime('%Y-%m-%d %H:%M:%S'),
        'server_id': 4
    }
]

def admin_required(f):
    """Декоратор для проверки авторизации админа"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Необходима авторизация администратора', 'error')
            return redirect(url_for('admin'))
        return f(*args, **kwargs)
    return decorated_function

def update_server_metrics():
    """Симуляция обновления метрик серверов"""
    for server in servers_data:
        if server['status'] == 'online':
            # Небольшие случайные изменения метрик
            server['cpu'] = max(0, min(100, server['cpu'] + random.randint(-5, 5)))
            server['memory'] = max(0, min(100, server['memory'] + random.randint(-3, 3)))
            server['network_in'] = max(0, server['network_in'] + random.randint(-100, 200))
            server['network_out'] = max(0, server['network_out'] + random.randint(-50, 150))
            server['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Добавляем данные о локальной машине
def get_local_server_data():
    """Получение данных о локальной машине"""
    if not SYSTEM_MONITOR_AVAILABLE:
        return {
            'id': 0,
            'name': 'Локальная машина (ограниченные данные)',
            'ip': '127.0.0.1',
            'port': 5000,
            'status': 'online',
            'cpu': 0,
            'memory': 0,
            'disk': 0,
            'network_in': 0,
            'network_out': 0,
            'uptime': 'Неизвестно',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'location': 'Локальная машина',
            'os': 'Неизвестно',
            'alerts': ['Системный мониторинг недоступен']
        }
    
    try:
        cpu_data = system_monitor.get_cpu_usage()
        memory_data = system_monitor.get_memory_usage()
        disk_data = system_monitor.get_disk_usage()
        network_data = system_monitor.get_network_usage()
        system_info = system_monitor.get_system_info()
        
        # Основной диск (первый в списке)
        main_disk = disk_data[0] if disk_data else {'percent': 0}
        
        return {
            'id': 0,
            'name': f'Локальная машина ({system_info.get("hostname", "Unknown")})',
            'ip': socket.gethostbyname(socket.gethostname()),
            'port': 5000,
            'status': 'online',
            'cpu': cpu_data.get('total', 0),
            'memory': memory_data.get('percent', 0),
            'disk': main_disk.get('percent', 0),
            'network_in': network_data.get('bytes_recv', 0),
            'network_out': network_data.get('bytes_sent', 0),
            'uptime': system_info.get('uptime', '0 дней 0 часов'),
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'location': 'Локальная машина',
            'os': f"{system_info.get('platform', 'Unknown')} {system_info.get('platform_release', '')}",
            'alerts': []
        }
    except Exception as e:
        logging.error(f"Ошибка получения данных локальной машины: {e}")
        return None

# Обновляем servers_data чтобы включить локальную машину
def update_servers_list():
    """Обновление списка серверов с локальной машиной"""
    global servers_data
    local_server = get_local_server_data()
    if local_server:
        # Удаляем старую запись локального сервера если есть
        servers_data = [s for s in servers_data if s['id'] != 0]
        # Добавляем обновленную запись в начало
        servers_data.insert(0, local_server)

# Основные маршруты
@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Эндпоинт проверки здоровья"""
    return jsonify({
        'статус': 'здоров',
        'сообщение': 'Приложение работает'
    })

@app.route('/api/status')
def status():
    """Эндпоинт статуса для мониторинга"""
    return jsonify({
        'приложение': 'мониторинг',
        'версия': '1.0.0',
        'статус': 'активно'
    })

@app.route('/servers')
def servers():
    """Страница списка серверов"""
    return render_template('servers.html', servers=servers_data)

# Импортируем админ модуль
try:
    from admin import admin_bp
    app.register_blueprint(admin_bp)
    ADMIN_MODULE_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Предупреждение: админ модуль недоступен - {e}")
    ADMIN_MODULE_AVAILABLE = False

@app.route('/api/servers')
def api_servers():
    """API для получения данных серверов"""
    return jsonify(servers_data)

@app.route('/admin/server/<int:server_id>/toggle', methods=['POST'])
def toggle_server_status(server_id):
    """Переключение статуса сервера (только для админа)"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Доступ запрещен'}), 403
    
    for server in servers_data:
        if server['id'] == server_id:
            server['status'] = 'offline' if server['status'] == 'online' else 'online'
            server['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            return jsonify({'success': True, 'new_status': server['status']})
    
    return jsonify({'error': 'Сервер не найден'}), 404

@app.route('/system')
def system_status():
    """Страница детального мониторинга локальной системы"""
    if not SYSTEM_MONITOR_AVAILABLE:
        return render_template('system_unavailable.html')
    
    report = system_monitor.get_full_report()
    return render_template('system_status.html', report=report)

@app.route('/api/system')
def api_system():
    """API для получения данных системы"""
    if not SYSTEM_MONITOR_AVAILABLE:
        return jsonify({'error': 'System monitor unavailable'})
    
    return jsonify(system_monitor.get_full_report())

@app.route('/api/servers/update')
def api_servers_update():
    """API для получения обновленных данных серверов"""
    update_servers_list()
    update_server_metrics()
    return jsonify({
        'servers': servers_data,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

@app.route('/api/notifications')
def api_notifications():
    """API для получения уведомлений"""
    return jsonify(notifications)

@app.route('/admin/notifications')
@admin_required
def admin_notifications():
    """Страница управления уведомлениями"""
    return render_template('admin_notifications.html', notifications=notifications)

@app.route('/admin/logs')
@admin_required
def admin_logs():
    """Страница просмотра логов"""
    try:
        with open('monitoring.log', 'r', encoding='utf-8') as f:
            logs = f.readlines()[-100:]  # Последние 100 строк
    except FileNotFoundError:
        logs = ['Файл логов не найден']
    
    return render_template('admin_logs.html', logs=logs)

@app.route('/admin/settings')
@admin_required
def admin_settings():
    """Страница настроек"""
    settings = {
        'check_interval': 30,
        'alert_threshold_cpu': 80,
        'alert_threshold_memory': 85,
        'alert_threshold_disk': 90,
        'email_notifications': True,
        'retention_days': 30
    }
    return render_template('admin_settings.html', settings=settings)

@app.route('/admin/server/add', methods=['GET', 'POST'])
@admin_required
def admin_add_server():
    """Добавление нового сервера"""
    if request.method == 'POST':
        new_server = {
            'id': max([s['id'] for s in servers_data]) + 1,
            'name': request.form.get('name'),
            'ip': request.form.get('ip'),
            'port': int(request.form.get('port', 80)),
            'status': 'online',
            'cpu': 0,
            'memory': 0,
            'disk': 0,
            'network_in': 0,
            'network_out': 0,
            'uptime': '0 дней 0 часов',
            'last_check': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'location': request.form.get('location', 'Не указано'),
            'os': request.form.get('os', 'Не указано'),
            'alerts': []
        }
        servers_data.append(new_server)
        logging.info(f"Добавлен новый сервер: {new_server['name']} ({new_server['ip']})")
        flash(f'Сервер {new_server["name"]} успешно добавлен!', 'success')
        return redirect(url_for('admin'))
    
    return render_template('admin_add_server.html')

# Обработчики ошибок
@app.errorhandler(404)
def not_found(error):
    return jsonify({'ошибка': 'Страница не найдена'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'ошибка': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    logging.info("Запуск приложения мониторинга")
    # Инициализируем список серверов с локальной машиной
    update_servers_list()
    # Запуск приложения
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    print(f"🚀 Запуск приложения мониторинга на {host}:{port}")
    app.run(
        host=host,
        port=port,
        debug=app.config['DEBUG']
    )
