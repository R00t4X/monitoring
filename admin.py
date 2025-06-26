from flask import Blueprint, render_template, request, jsonify, session, flash, redirect, url_for
from functools import wraps
import json
import os
from datetime import datetime, timedelta
import logging

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

# Данные пользователей (в реальном приложении - база данных)
users_data = [
    {
        'id': 1,
        'username': 'admin',
        'password': 'admin123',  # В реальности - хеш
        'role': 'administrator',
        'email': 'admin@monitoring.local',
        'created': '2024-01-01 00:00:00',
        'last_login': None,
        'active': True
    },
    {
        'id': 2,
        'username': 'operator',
        'password': 'op123',
        'role': 'operator',
        'email': 'operator@monitoring.local',
        'created': '2024-01-15 10:30:00',
        'last_login': '2024-01-15 15:45:00',
        'active': True
    }
]

# Настройки системы
system_settings = {
    'monitoring_interval': 30,
    'alert_cpu_threshold': 80,
    'alert_memory_threshold': 85,
    'alert_disk_threshold': 90,
    'email_notifications': True,
    'sms_notifications': False,
    'log_retention_days': 30,
    'max_servers': 50,
    'enable_api': True,
    'maintenance_mode': False
}

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'admin_logged_in' not in session:
            flash('Требуется авторизация администратора', 'error')
            return redirect(url_for('admin.login'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/')
def dashboard():
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin.login'))
    
    # Получаем статистику для dashboard
    from app import servers_data, notifications
    
    stats = {
        'total_servers': len(servers_data),
        'online_servers': len([s for s in servers_data if s['status'] == 'online']),
        'offline_servers': len([s for s in servers_data if s['status'] == 'offline']),
        'warning_servers': len([s for s in servers_data if s['status'] == 'warning']),
        'total_alerts': len(notifications),
        'critical_alerts': len([n for n in notifications if n['type'] == 'error']),
        'total_users': len(users_data),
        'active_users': len([u for u in users_data if u['active']])
    }
    
    return render_template('admin/dashboard.html', stats=stats, settings=system_settings)

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = next((u for u in users_data if u['username'] == username and u['password'] == password), None)
        
        if user and user['active']:
            session['admin_logged_in'] = True
            session['admin_user'] = user
            user['last_login'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            flash('Успешный вход в систему!', 'success')
            logging.info(f"Admin login: {username}")
            return redirect(url_for('admin.dashboard'))
        else:
            flash('Неверный логин или пароль!', 'error')
            logging.warning(f"Failed admin login attempt: {username}")
    
    return render_template('admin/login.html')

@admin_bp.route('/logout')
def logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_user', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('admin.login'))

@admin_bp.route('/servers')
@admin_required
def servers():
    from app import servers_data
    return render_template('admin/servers.html', servers=servers_data)

@admin_bp.route('/servers/add', methods=['GET', 'POST'])
@admin_required
def add_server():
    if request.method == 'POST':
        from app import servers_data
        
        new_server = {
            'id': max([s['id'] for s in servers_data]) + 1 if servers_data else 1,
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
        logging.info(f"Server added: {new_server['name']} ({new_server['ip']})")
        flash(f'Сервер {new_server["name"]} добавлен!', 'success')
        return redirect(url_for('admin.servers'))
    
    return render_template('admin/add_server.html')

@admin_bp.route('/servers/<int:server_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_server(server_id):
    from app import servers_data
    
    server = next((s for s in servers_data if s['id'] == server_id), None)
    if not server:
        flash('Сервер не найден', 'error')
        return redirect(url_for('admin.servers'))
    
    if request.method == 'POST':
        server['name'] = request.form.get('name')
        server['ip'] = request.form.get('ip')
        server['port'] = int(request.form.get('port', 80))
        server['location'] = request.form.get('location')
        server['os'] = request.form.get('os')
        
        logging.info(f"Server updated: {server['name']} ({server['ip']})")
        flash('Сервер обновлен!', 'success')
        return redirect(url_for('admin.servers'))
    
    return render_template('admin/edit_server.html', server=server)

@admin_bp.route('/servers/<int:server_id>/delete', methods=['POST'])
@admin_required
def delete_server(server_id):
    from app import servers_data
    
    server = next((s for s in servers_data if s['id'] == server_id), None)
    if server:
        servers_data.remove(server)
        logging.info(f"Server deleted: {server['name']} ({server['ip']})")
        flash('Сервер удален!', 'success')
    else:
        flash('Сервер не найден', 'error')
    
    return redirect(url_for('admin.servers'))

@admin_bp.route('/users')
@admin_required
def users():
    return render_template('admin/users.html', users=users_data)

@admin_bp.route('/users/add', methods=['GET', 'POST'])
@admin_required
def add_user():
    if request.method == 'POST':
        new_user = {
            'id': max([u['id'] for u in users_data]) + 1,
            'username': request.form.get('username'),
            'password': request.form.get('password'),  # В реальности - хеш
            'role': request.form.get('role'),
            'email': request.form.get('email'),
            'created': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'last_login': None,
            'active': True
        }
        
        users_data.append(new_user)
        logging.info(f"User added: {new_user['username']}")
        flash(f'Пользователь {new_user["username"]} добавлен!', 'success')
        return redirect(url_for('admin.users'))
    
    return render_template('admin/add_user.html')

@admin_bp.route('/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):
    user = next((u for u in users_data if u['id'] == user_id), None)
    if user:
        user['active'] = not user['active']
        status = 'активирован' if user['active'] else 'деактивирован'
        logging.info(f"User {status}: {user['username']}")
        flash(f'Пользователь {user["username"]} {status}!', 'success')
    
    return redirect(url_for('admin.users'))

@admin_bp.route('/settings', methods=['GET', 'POST'])
@admin_required
def settings():
    if request.method == 'POST':
        # Обновляем настройки
        system_settings.update({
            'monitoring_interval': int(request.form.get('monitoring_interval', 30)),
            'alert_cpu_threshold': int(request.form.get('alert_cpu_threshold', 80)),
            'alert_memory_threshold': int(request.form.get('alert_memory_threshold', 85)),
            'alert_disk_threshold': int(request.form.get('alert_disk_threshold', 90)),
            'email_notifications': 'email_notifications' in request.form,
            'sms_notifications': 'sms_notifications' in request.form,
            'log_retention_days': int(request.form.get('log_retention_days', 30)),
            'max_servers': int(request.form.get('max_servers', 50)),
            'enable_api': 'enable_api' in request.form,
            'maintenance_mode': 'maintenance_mode' in request.form
        })
        
        logging.info("System settings updated")
        flash('Настройки сохранены!', 'success')
        return redirect(url_for('admin.settings'))
    
    return render_template('admin/settings.html', settings=system_settings)

@admin_bp.route('/logs')
@admin_required
def logs():
    try:
        with open('monitoring.log', 'r', encoding='utf-8') as f:
            logs = f.readlines()[-200:]  # Последние 200 строк
        logs.reverse()  # Новые сверху
    except FileNotFoundError:
        logs = ['Файл логов не найден']
    
    return render_template('admin/logs.html', logs=logs)

@admin_bp.route('/alerts')
@admin_required
def alerts():
    from app import notifications
    return render_template('admin/alerts.html', alerts=notifications)

@admin_bp.route('/analytics')
@admin_required
def analytics():
    from app import servers_data
    
    # Генерируем аналитику
    analytics_data = {
        'cpu_usage': [s['cpu'] for s in servers_data if s['status'] == 'online'],
        'memory_usage': [s['memory'] for s in servers_data if s['status'] == 'online'],
        'disk_usage': [s['disk'] for s in servers_data if s['status'] == 'online'],
        'server_locations': {},
        'os_distribution': {}
    }
    
    # Подсчитываем распределение по локациям и ОС
    for server in servers_data:
        location = server.get('location', 'Неизвестно')
        os_name = server.get('os', 'Неизвестно')
        
        analytics_data['server_locations'][location] = analytics_data['server_locations'].get(location, 0) + 1
        analytics_data['os_distribution'][os_name] = analytics_data['os_distribution'].get(os_name, 0) + 1
    
    return render_template('admin/analytics.html', analytics=analytics_data)

@admin_bp.route('/backup')
@admin_required
def backup():
    """Создание резервной копии данных"""
    backup_data = {
        'servers': [],  # В реальности - из БД
        'users': users_data,
        'settings': system_settings,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    
    # Сохраняем бэкап
    backup_filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    try:
        with open(backup_filename, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        logging.info(f"Backup created: {backup_filename}")
        flash(f'Резервная копия создана: {backup_filename}', 'success')
    except Exception as e:
        logging.error(f"Backup failed: {e}")
        flash('Ошибка создания резервной копии', 'error')
    
    return redirect(url_for('admin.dashboard'))
