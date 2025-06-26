"""
Основной файл приложения - перенаправляет на simple_app.py
"""
import sys
import os

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("⚠️ Использование app.py устарело. Запускайте simple_app.py")
print("🔄 Перенаправление на simple_app.py...")

# Импортируем и запускаем упрощенное приложение
try:
    from simple_app import app
    
    if __name__ == '__main__':
        app.run(host='127.0.0.1', port=5000, debug=True)
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("📋 Убедитесь, что файл simple_app.py существует")
    SQLAlchemy = None

# Безопасный импорт system_monitor
try:
    from system_monitor import system_monitor
    SYSTEM_MONITOR_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Предупреждение: system_monitor недоступен - {e}")
    SYSTEM_MONITOR_AVAILABLE = False
    system_monitor = None

# Import advanced monitoring components
try:
    from advanced_monitor import advanced_monitor
    from alert_system import alert_manager, EmailNotifier, SlackNotifier
    if SQLALCHEMY_AVAILABLE:
        from models import db, Server, ServerMetric, Alert as DBAlert, MonitoringConfig
    ADVANCED_MONITORING_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Advanced monitoring components not available: {e}")
    ADVANCED_MONITORING_AVAILABLE = False
    # Create mock objects
    if SQLALCHEMY_AVAILABLE:
        class MockDB:
            def init_app(self, app): pass
            def create_all(self): pass
        db = MockDB()

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('monitoring.log'),
        logging.StreamHandler()
    ]
)

# Создание приложения Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Конфигурация базы данных (только если SQLAlchemy доступна)
if SQLALCHEMY_AVAILABLE:
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///monitoring.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация расширений
if SQLALCHEMY_AVAILABLE and 'db' in locals():
    db.init_app(app)

# Инициализация SocketIO (только если доступна)
if SOCKETIO_AVAILABLE:
    socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')
else:
    socketio = None

# Базовая конфигурация
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

if ADVANCED_MONITORING_AVAILABLE:
    @app.route('/api/realtime/metrics')
    def realtime_metrics():
        """Real-time metrics endpoint"""
        metrics = advanced_monitor.get_comprehensive_metrics()
        
        # Проверяем алерты
        alert_manager.check_metrics(metrics)
        
        return jsonify({
            'metrics': metrics,
            'alerts': [alert.to_dict() for alert in alert_manager.get_active_alerts()],
            'timestamp': datetime.now().isoformat()
        })
    
    @app.route('/api/metrics/history/<metric_type>')
    def metrics_history(metric_type):
        """История метрик"""
        limit = request.args.get('limit', 100, type=int)
        history = advanced_monitor.get_metrics_history(metric_type, limit)
        return jsonify(history)
    
    @app.route('/api/metrics/trends/<metric_type>/<field>')
    def metrics_trends(metric_type, field):
        """Тренды метрик"""
        period = request.args.get('period', 60, type=int)
        trends = advanced_monitor.calculate_trends(metric_type, field, period)
        return jsonify(trends)
    
    @app.route('/advanced-dashboard')
    def advanced_dashboard():
        """Продвинутая панель мониторинга"""
        return render_template('advanced_dashboard.html')
    
    if ADVANCED_MONITORING_AVAILABLE and SOCKETIO_AVAILABLE:
        @socketio.on('connect')
        def handle_connect():
            """Обработка подключения WebSocket"""
            print('Client connected')
            emit('status', {'msg': 'Connected to monitoring system'})
        
        @socketio.on('disconnect')
        def handle_disconnect():
            """Обработка отключения WebSocket"""
            print('Client disconnected')
        
        @socketio.on('request_metrics')
        def handle_metrics_request():
            """Обработка запроса метрик через WebSocket"""
            metrics = advanced_monitor.get_comprehensive_metrics()
            emit('metrics_update', metrics)

    def broadcast_metrics(metrics):
        """Broadcast метрик всем подключенным клиентам"""
        socketio.emit('metrics_update', metrics)
    
    # Добавляем колбэк для трансляции метрик
    advanced_monitor.add_callback(broadcast_metrics)

# Замена deprecated @app.before_first_request на @app.before_request с проверкой
@app.before_request
def before_first_request():
    """Инициализация при первом запросе"""
    if not hasattr(app, '_initialized'):
        app._initialized = True
        create_tables()

def create_tables():
    """Создание таблиц базы данных"""
    if ADVANCED_MONITORING_AVAILABLE:
        with app.app_context():
            db.create_all()
            
            # Запускаем продвинутый мониторинг
            advanced_monitor.start_monitoring(interval=30)
            
            # Настройка уведомлений (пример)
            # email_notifier = EmailNotifier(
            #     smtp_server="smtp.gmail.com",
            #     smtp_port=587,
            #     username="your-email@gmail.com",
            #     password="your-password",
            #     from_email="monitoring@yourcompany.com",
            #     to_emails=["admin@yourcompany.com"]
            # )
            # alert_manager.add_notifier(email_notifier)

# Запуск приложения
if __name__ == '__main__':
    logging.info("Запуск продвинутой системы мониторинга")
    
    if ADVANCED_MONITORING_AVAILABLE and SOCKETIO_AVAILABLE:
        socketio.run(app, host='127.0.0.1', port=5000, debug=True)
    else:
        print("⚠️ Запуск в упрощенном режиме (без WebSocket)")
        app.run(host='127.0.0.1', port=5000, debug=True)
