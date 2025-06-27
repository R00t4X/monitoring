"""
Основное приложение системы мониторинга.
"""
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import os
import sys
import logging
from datetime import datetime

# Добавляем src в путь для импортов
sys.path.append(os.path.dirname(__file__))

from core.system_monitor import SystemMonitor
from core.database import DatabaseManager
from core.ssh_monitor import SSHMonitor
from core.monitor_scheduler import MonitorScheduler

# Создание Flask приложения
app = Flask(__name__, 
            template_folder='../templates',
            static_folder='../static')

app.config['SECRET_KEY'] = 'monitoring-secret-key-2024'
app.config['JSON_AS_ASCII'] = False

# Инициализация компонентов
system_monitor = SystemMonitor()
db_manager = DatabaseManager()
ssh_monitor = SSHMonitor()
scheduler = MonitorScheduler(db_manager, ssh_monitor)

# Автозапуск планировщика при инициализации (только при первом запуске)
_monitoring_initialized = False

def init_monitoring():
    """Инициализация автоматического мониторинга"""
    global _monitoring_initialized
    
    # Запускаем только при первой инициализации, не при hot reload
    if not _monitoring_initialized and not scheduler.running:
        scheduler.start(interval=60)
        print("🔄 Автоматический мониторинг инициализирован (интервал: 60 секунд)")
        _monitoring_initialized = True

# Запускаем инициализацию
init_monitoring()

# Функция для загрузки админских данных
def load_admin_credentials():
    """Загружает учетные данные администратора из файла"""
    credentials_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ADMIN_CREDENTIALS.txt')
    try:
        if os.path.exists(credentials_file):
            with open(credentials_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # Ищем логин и пароль в файле
                username = None
                password = None
                for line in content.split('\n'):
                    line = line.strip()
                    if line.startswith('ЛОГИН:'):
                        username = line.split(':', 1)[1].strip()
                    elif line.startswith('ПАРОЛЬ:'):
                        password = line.split(':', 1)[1].strip()
                
                if username and password:
                    return {'username': username, 'password': password}
        
        # Если файл не найден или данные не прочитались, используем значения по умолчанию
        logging.warning("ADMIN_CREDENTIALS.txt не найден или повреждён. Используются данные по умолчанию.")
        return {'username': 'admin', 'password': 'admin123'}
    except Exception as e:
        logging.error(f"Ошибка чтения файла учетных данных: {e}")
        return {'username': 'admin', 'password': 'admin123'}

# Загружаем админские данные
ADMIN_USER = load_admin_credentials()

@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/system')
def system_status():
    """Системный мониторинг"""
    try:
        metrics = system_monitor.get_all_metrics()
        return render_template('system.html', report=metrics)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/servers')
def servers():
    """Публичная страница серверов (только просмотр)"""
    try:
        servers = db_manager.get_all_servers()
        return render_template('servers_public.html', servers=servers)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/admin/servers')
def admin_servers():
    """Административная страница серверов (полное управление)"""
    if 'admin' not in session:
        return redirect(url_for('admin'))
    
    try:
        servers = db_manager.get_all_servers()
        return render_template('admin_servers.html', servers=servers)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/admin')
def admin():
    """Главная страница админки (дашборд)"""
    if 'admin' in session:
        servers = db_manager.get_all_servers()
        return render_template('admin.html', servers=servers)
    return render_template('login.html')

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    """Вход в админку"""
    if request.method == 'GET':
        # Отображаем форму входа
        return render_template('login.html')
    
    # Обработка POST-запроса
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_USER['username'] and password == ADMIN_USER['password']:
        session['admin'] = True
        return redirect(url_for('admin'))
    
    flash('Неверные данные', 'error')
    return redirect(url_for('admin_login'))

@app.route('/admin/logout')
def admin_logout():
    """Выход из админки"""
    session.pop('admin', None)
    return redirect(url_for('index'))

@app.route('/admin/servers/add', methods=['GET', 'POST'])
def admin_add_server():
    """Добавление сервера"""
    if 'admin' not in session:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        server_data = {
            'name': request.form.get('name'),
            'ip': request.form.get('ip'),
            'port': int(request.form.get('port', 22)),
            'username': request.form.get('username', 'root'),
            'description': request.form.get('description', '')
        }
        
        # Добавляем данные аутентификации
        auth_method = request.form.get('auth_method', 'key')
        if auth_method == 'password':
            server_data['password'] = request.form.get('password')
            server_data['ssh_key_path'] = None
            server_data['ssh_key_content'] = None
        else:
            server_data['password'] = None
            server_data['ssh_key_path'] = request.form.get('ssh_key_path') if request.form.get('ssh_key_path') else None
            server_data['ssh_key_content'] = request.form.get('ssh_key_content') if request.form.get('ssh_key_content') else None
        
        try:
            db_manager.add_server(server_data)
            flash('Сервер добавлен', 'success')
            return redirect(url_for('admin_servers'))
        except Exception as e:
            flash(f'Ошибка: {e}', 'error')
    
    return render_template('add_server.html')

@app.route('/admin/servers/<int:server_id>/edit', methods=['GET', 'POST'])
def admin_edit_server(server_id):
    """Редактирование сервера"""
    if 'admin' not in session:
        return redirect(url_for('admin'))
    
    server = db_manager.get_server(server_id)
    if not server:
        flash('Сервер не найден', 'error')
        return redirect(url_for('admin_servers'))
    
    if request.method == 'POST':
        server_data = {
            'name': request.form.get('name'),
            'ip': request.form.get('ip'),
            'port': int(request.form.get('port', 22)),
            'username': request.form.get('username', 'root'),
            'description': request.form.get('description', '')
        }
        
        try:
            db_manager.update_server(server_id, server_data)
            flash('Сервер обновлен', 'success')
            return redirect(url_for('admin_servers'))
        except Exception as e:
            flash(f'Ошибка: {e}', 'error')
    
    return render_template('edit_server.html', server=server)

@app.route('/admin/servers/<int:server_id>/delete', methods=['POST'])
def admin_delete_server(server_id):
    """Удаление сервера"""
    if 'admin' not in session:
        return redirect(url_for('admin'))
    
    try:
        db_manager.delete_server(server_id)
        flash('Сервер удален', 'success')
    except Exception as e:
        flash(f'Ошибка: {e}', 'error')
    
    return redirect(url_for('admin_servers'))

@app.route('/admin/servers/<int:server_id>/test')
def admin_test_server(server_id):
    """Тестирование SSH подключения"""
    if 'admin' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    server = db_manager.get_server(server_id)
    if not server:
        return jsonify({'error': 'Сервер не найден'}), 404
    
    result = ssh_monitor.test_connection(
        host=server['ip'],
        port=server['port'],
        username=server['username']
    )
    
    return jsonify(result)

@app.route('/admin/servers/<int:server_id>/metrics')
def admin_server_current_metrics(server_id):
    """API текущих метрик сервера"""
    if 'admin' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        # Получаем информацию о сервере
        server = db_manager.get_server(server_id)
        if not server:
            return jsonify({'error': 'Сервер не найден'}), 404
        
        # Получаем метрики через SSH
        ssh_monitor = SSHMonitor()
        metrics = ssh_monitor.get_metrics(
            server['ip'], 
            server['port'], 
            server['username'], 
            server.get('password'),
            server.get('ssh_key_path'),
            server.get('ssh_key_content')
        )
        
        if metrics and 'error' not in metrics:
            return jsonify({
                'cpu': round(metrics.get('cpu', 0), 1),
                'memory': round(metrics.get('memory', 0), 1),
                'disk': round(metrics.get('disk', 0), 1),
                'status': 'online'
            })
        else:
            return jsonify({
                'cpu': 0,
                'memory': 0,
                'disk': 0,
                'status': 'offline',
                'error': metrics.get('error', 'Недоступен') if metrics else 'Недоступен'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/metrics')
def api_metrics():
    """API метрик"""
    try:
        metrics = system_monitor.get_all_metrics()
        return jsonify(metrics)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers')
def api_servers():
    """API списка серверов"""
    try:
        servers = db_manager.get_all_servers()
        return jsonify({'servers': servers, 'count': len(servers)})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<int:server_id>/metrics')
def api_server_metrics(server_id):
    """API истории метрик сервера"""
    try:
        metrics = db_manager.get_server_metrics(server_id)
        return jsonify({'metrics': metrics})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/servers/<int:server_id>/status')
def api_server_status(server_id):
    """API публичного статуса сервера (без авторизации)"""
    try:
        server = db_manager.get_server(server_id)
        if not server:
            return jsonify({'error': 'Сервер не найден'}), 404
        
        # Получаем последние метрики из базы (если есть)
        latest_metrics = db_manager.get_server_metrics(server_id, limit=1)
        
        if latest_metrics:
            metric = latest_metrics[0]
            return jsonify({
                'cpu': round(metric.get('cpu_percent', 0), 1),
                'memory': round(metric.get('memory_percent', 0), 1),
                'disk': round(metric.get('disk_percent', 0), 1),
                'status': server.get('status', 'unknown'),
                'last_update': metric.get('timestamp'),
                'source': 'database'
            })
        else:
            return jsonify({
                'cpu': 0,
                'memory': 0,
                'disk': 0,
                'status': server.get('status', 'unknown'),
                'last_update': server.get('last_check'),
                'source': 'server_info',
                'message': 'Нет сохраненных метрик. Войдите в админку для получения актуальных данных.'
            })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/monitoring/start')
def admin_start_monitoring():
    """Запуск автоматического мониторинга"""
    if 'admin' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        scheduler.start()
        return jsonify({'success': True, 'message': 'Мониторинг запущен'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/monitoring/stop')
def admin_stop_monitoring():
    """Остановка автоматического мониторинга"""
    if 'admin' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        scheduler.stop()
        return jsonify({'success': True, 'message': 'Мониторинг остановлен'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/monitoring/status')
def admin_monitoring_status():
    """Статус мониторинга"""
    if 'admin' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    return jsonify({
        'running': scheduler.running,
        'interval': scheduler.interval,
        'servers_count': len(db_manager.get_all_servers()),
        'thread_alive': scheduler.thread.is_alive() if scheduler.thread else False
    })

@app.route('/admin/monitoring/set-interval', methods=['POST'])
def admin_set_monitoring_interval():
    """Изменение интервала мониторинга"""
    if 'admin' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    try:
        data = request.get_json()
        interval = int(data.get('interval', 300))
        
        if interval < 60:  # Минимум 1 минута
            return jsonify({'error': 'Интервал не может быть меньше 60 секунд'}), 400
        
        scheduler.set_interval(interval)
        return jsonify({
            'success': True, 
            'message': f'Интервал изменен на {interval} секунд',
            'interval': interval
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/servers/<int:server_id>/history')
def admin_server_history(server_id):
    """История метрик сервера"""
    if 'admin' not in session:
        return redirect(url_for('admin'))
    
    server = db_manager.get_server(server_id)
    if not server:
        flash('Сервер не найден', 'error')
        return redirect(url_for('admin_servers'))
    
    metrics = db_manager.get_server_metrics(server_id, limit=50)
    return render_template('server_history.html', server=server, metrics=metrics)

@app.route('/servers/<int:server_id>')
def server_detail(server_id):
    """Детальная информация о сервере"""
    try:
        server = db_manager.get_server(server_id)
        if not server:
            return render_template('error.html', error='Сервер не найден'), 404
        
        # Получаем последние метрики сервера
        latest_metrics = db_manager.get_server_metrics(server_id, limit=1)
        
        # Получаем статистику за последние 24 часа
        metrics_24h = db_manager.get_server_metrics(server_id, limit=100)
        
        return render_template('server_detail.html', 
                             server=server, 
                             latest_metrics=latest_metrics[0] if latest_metrics else None,
                             metrics_24h=metrics_24h,
                             is_admin=('admin' in session))
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/api/servers/<int:server_id>/test-connection')
def api_test_server_connection(server_id):
    """API для тестирования SSH подключения к серверу"""
    try:
        server = db_manager.get_server(server_id)
        if not server:
            return jsonify({'error': 'Сервер не найден'}), 404
        
        ssh_monitor = SSHMonitor()
        
        # Сначала тестируем подключение
        test_result = ssh_monitor.test_connection(
            server['ip'], 
            server['port'], 
            server['username'], 
            server.get('password'),
            server.get('ssh_key_path'),
            server.get('ssh_key_content')
        )
        
        if test_result['success']:
            # Если подключение успешно, получаем метрики
            metrics = ssh_monitor.get_metrics(
                server['ip'], 
                server['port'], 
                server['username'], 
                server.get('password'),
                server.get('ssh_key_path'),
                server.get('ssh_key_content')
            )
        
        if metrics and 'error' not in metrics:
            return jsonify({
                'success': True,
                'status': 'online',
                'message': 'SSH подключение успешно',
                'metrics': {
                    'cpu': round(metrics.get('cpu', 0), 1),
                    'memory': round(metrics.get('memory', 0), 1),
                    'disk': round(metrics.get('disk', 0), 1)
                }
            })
        else:
            return jsonify({
                'success': False,
                'status': 'offline',
                'message': f"SSH недоступен: {metrics.get('error', 'Неизвестная ошибка') if metrics else 'Нет ответа'}"
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'error',
            'message': f'Ошибка тестирования: {str(e)}'
        }), 500

if __name__ == '__main__':
    # Запускаем планировщик при старте с интервалом 60 секунд
    scheduler.start(interval=60)
    print(f"🔄 Автоматический мониторинг запущен (интервал: 60 секунд)")
    
    # Получаем порт из переменной окружения или используем по умолчанию
    port = int(os.environ.get('PORT', 5000))
    
    app.run(host='127.0.0.1', port=port, debug=True)
