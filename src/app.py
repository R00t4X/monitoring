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

# Админские данные
ADMIN_USER = {'username': 'admin', 'password': 'admin123'}

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
    """Список серверов"""
    try:
        servers = db_manager.get_all_servers()
        return render_template('servers.html', servers=servers)
    except Exception as e:
        return render_template('error.html', error=str(e))

@app.route('/admin')
def admin():
    """Админка"""
    if 'admin' in session:
        servers = db_manager.get_all_servers()
        return render_template('admin.html', servers=servers)
    return render_template('login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login():
    """Вход в админку"""
    username = request.form.get('username')
    password = request.form.get('password')
    
    if username == ADMIN_USER['username'] and password == ADMIN_USER['password']:
        session['admin'] = True
        return redirect(url_for('admin'))
    
    flash('Неверные данные', 'error')
    return redirect(url_for('admin'))

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
        
        try:
            db_manager.add_server(server_data)
            flash('Сервер добавлен', 'success')
            return redirect(url_for('admin'))
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
        return redirect(url_for('admin'))
    
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
            return redirect(url_for('admin'))
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
    
    return redirect(url_for('admin'))

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
def admin_get_server_metrics(server_id):
    """Получение метрик сервера через SSH"""
    if 'admin' not in session:
        return jsonify({'error': 'Не авторизован'}), 401
    
    server = db_manager.get_server(server_id)
    if not server:
        return jsonify({'error': 'Сервер не найден'}), 404
    
    metrics = ssh_monitor.get_metrics(
        host=server['ip'],
        port=server['port'],
        username=server['username']
    )
    
    return jsonify(metrics)

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
        'servers_count': len(db_manager.get_all_servers())
    })

@app.route('/admin/servers/<int:server_id>/history')
def admin_server_history(server_id):
    """История метрик сервера"""
    if 'admin' not in session:
        return redirect(url_for('admin'))
    
    server = db_manager.get_server(server_id)
    if not server:
        flash('Сервер не найден', 'error')
        return redirect(url_for('admin'))
    
    metrics = db_manager.get_server_metrics(server_id, limit=50)
    return render_template('server_history.html', server=server, metrics=metrics)

if __name__ == '__main__':
    # Запускаем планировщик при старте
    scheduler.start()
    app.run(host='127.0.0.1', port=5000, debug=True)
