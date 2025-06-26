#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Упрощенная версия приложения мониторинга без сложных зависимостей.
"""
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, flash
import os
import random
import socket
import sys  # Added missing import
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
    from system_monitor import SystemMonitor
    system_monitor = SystemMonitor()
    SYSTEM_MONITOR_AVAILABLE = True
    logging.info("System monitor загружен успешно")
except ImportError as e:
    logging.warning(f"System monitor недоступен: {e}")
    SYSTEM_MONITOR_AVAILABLE = False
    system_monitor = None

# Импортируем менеджер серверов
try:
    from server_manager import server_manager
    SERVER_MANAGER_AVAILABLE = True
except ImportError as e:
    SERVER_MANAGER_AVAILABLE = False
    logging.warning(f"Server manager недоступен: {e}")

# Импортируем менеджер базы данных
try:
    from database import db_manager
    DATABASE_AVAILABLE = True
    logging.info("База данных доступна")
except ImportError as e:
    DATABASE_AVAILABLE = False
    logging.warning(f"База данных недоступна: {e}")

# Импортируем SSH монитор
try:
    from ssh_monitor import ssh_monitor
    SSH_MONITOR_AVAILABLE = True
    logging.info("SSH мониторинг доступен")
except ImportError as e:
    SSH_MONITOR_AVAILABLE = False
    logging.warning(f"SSH мониторинг недоступен: {e}")

# Создание экземпляра Flask приложения
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Настройка Flask для правильной работы с UTF-8
app.config['JSON_AS_ASCII'] = False

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
    if SERVER_MANAGER_AVAILABLE:
        # Получаем серверы из менеджера
        servers = server_manager.get_all_servers()
    else:
        # Fallback данные если менеджер недоступен
        servers = []
    
    # Добавляем локальную машину в начало списка
    local_server = get_local_server_data()
    if local_server:
        # Убираем локальный сервер если он уже есть в списке
        servers = [s for s in servers if s.get('id') != 0]
        servers.insert(0, local_server)
    
    return servers

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
    servers_data = get_servers_data()
    return render_template('servers.html', servers=servers_data)

@app.route('/system')
def system_status():
    """Страница детального мониторинга локальной системы"""
    try:
        if not SYSTEM_MONITOR_AVAILABLE:
            # Показываем страницу с информацией о недоступности
            return render_template('system_unavailable.html', 
                                 error="System monitor недоступен",
                                 suggestions=[
                                     "Запустите автонастройку: <code>python3 auto_install.py</code>",
                                     "Или установите зависимости вручную: <code>pip install psutil py-cpuinfo</code>",
                                     "Перезапустите приложение"
                                 ])
        
        # Пытаемся получить данные мониторинга
        report = system_monitor.get_all_metrics()
        
        # Проверяем, что получили валидные данные
        if not report or not isinstance(report, dict):
            raise Exception("Получены некорректные данные мониторинга")
        
        return render_template('system_status.html', report=report)
        
    except Exception as e:
        logging.error(f"Ошибка получения системных метрик: {e}")
        # Показываем страницу с ошибкой и предложениями решения
        return render_template('system_unavailable.html', 
                             error=str(e),
                             suggestions=[
                                 "Запустите автонастройку: <code>python3 auto_install.py</code>",
                                 "Проверьте установку зависимостей: <code>pip list | grep psutil</code>",
                                 "Перезапустите приложение в виртуальном окружении"
                             ])

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
    servers_data = get_servers_data()
    return jsonify({
        'servers': servers_data,
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    })

# Новые маршруты для управления серверами
@app.route('/admin/servers')
def admin_servers():
    """Админка - управление серверами"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))
    
    servers_data = get_servers_data()
    return render_template('admin_servers.html', servers=servers_data)

@app.route('/admin/servers/add', methods=['GET', 'POST'])
def admin_add_server():
    """Добавление сервера"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))
    
    if request.method == 'POST':
        if not SERVER_MANAGER_AVAILABLE:
            flash('Менеджер серверов недоступен', 'error')
            return redirect(url_for('admin_servers'))
        
        server_data = {
            'name': request.form.get('name', '').strip(),
            'ip': request.form.get('ip', '').strip(),
            'port': int(request.form.get('port', 22)),
            'location': request.form.get('location', '').strip(),
            'os': request.form.get('os', '').strip(),
            'description': request.form.get('description', '').strip(),
            # SSH данные
            'username': request.form.get('username', 'root').strip(),
            'auth_method': request.form.get('auth_method', 'key'),
            'password': request.form.get('password', '').strip() if request.form.get('auth_method') == 'password' else None,
            'key_path': request.form.get('key_path', '').strip() if request.form.get('auth_method') == 'key' else None
        }
        
        # Валидация
        if not server_data['name'] or not server_data['ip']:
            flash('Название и IP адрес обязательны', 'error')
            return render_template('admin_add_server.html', server=server_data)
        
        # Тестируем SSH подключение если включен мониторинг
        ssh_test_result = None
        if SSH_MONITOR_AVAILABLE and request.form.get('test_ssh'):
            ssh_test_result = ssh_monitor.test_ssh_connection(
                host=server_data['ip'],
                port=server_data['port'],
                username=server_data['username'],
                key_path=server_data['key_path'],
                password=server_data['password']
            )
            
            if not ssh_test_result['success']:
                flash(f'SSH тест не пройден: {ssh_test_result["error"]}', 'error')
                if 'suggestion' in ssh_test_result:
                    flash(f'Рекомендация: {ssh_test_result["suggestion"]}', 'info')
                return render_template('admin_add_server.html', server=server_data, ssh_test=ssh_test_result)
        
        try:
            new_server = server_manager.add_server(server_data)
            flash(f'Сервер "{new_server["name"]}" добавлен!', 'success')
            
            # Если SSH тест прошел успешно, сразу получаем метрики
            if ssh_test_result and ssh_test_result['success'] and SSH_MONITOR_AVAILABLE:
                metrics = ssh_monitor.get_server_metrics(
                    host=server_data['ip'],
                    port=server_data['port'],
                    username=server_data['username'],
                    key_path=server_data['key_path'],
                    password=server_data['password']
                )
                
                # Обновляем метрики сервера
                server_manager.update_server_metrics(new_server['id'], metrics)
                flash('Метрики сервера получены через SSH', 'success')
                
                # Запускаем мониторинг если нужно
                if request.form.get('start_monitoring'):
                    ssh_monitor.start_monitoring_server(new_server, interval=300)  # 5 минут
                    flash('Автоматический мониторинг запущен', 'success')
            
            logging.info(f"Добавлен сервер: {new_server['name']} ({new_server['ip']})")
            return redirect(url_for('admin_servers'))
            
        except Exception as e:
            flash(f'Ошибка добавления сервера: {e}', 'error')
    
    return render_template('admin_add_server.html')

@app.route('/admin/servers/<int:server_id>/edit', methods=['GET', 'POST'])
def admin_edit_server(server_id):
    """Редактирование сервера"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))
    
    if not SERVER_MANAGER_AVAILABLE:
        flash('Менеджер серверов недоступен', 'error')
        return redirect(url_for('admin_servers'))
    
    server = server_manager.get_server_by_id(server_id)
    if not server:
        flash('Сервер не найден', 'error')
        return redirect(url_for('admin_servers'))
    
    if request.method == 'POST':
        server_data = {
            'name': request.form.get('name', '').strip(),
            'ip': request.form.get('ip', '').strip(),
            'port': int(request.form.get('port', 80)),
            'location': request.form.get('location', '').strip(),
            'os': request.form.get('os', '').strip(),
            'description': request.form.get('description', '').strip()
        }
        
        if not server_data['name'] or not server_data['ip']:
            flash('Название и IP адрес обязательны', 'error')
            return render_template('admin_edit_server.html', server=server)
        
        try:
            if server_manager.update_server(server_id, server_data):
                flash(f'Сервер "{server_data["name"]}" обновлен!', 'success')
                logging.info(f"Обновлен сервер: {server_data['name']} ({server_data['ip']})")
                return redirect(url_for('admin_servers'))
            else:
                flash('Ошибка обновления сервера', 'error')
        except Exception as e:
            flash(f'Ошибка обновления сервера: {e}', 'error')
    
    return render_template('admin_edit_server.html', server=server)

@app.route('/admin/servers/<int:server_id>/delete', methods=['POST'])
def admin_delete_server(server_id):
    """Удаление сервера"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))
    
    if not SERVER_MANAGER_AVAILABLE:
        flash('Менеджер серверов недоступен', 'error')
        return redirect(url_for('admin_servers'))
    
    server = server_manager.get_server_by_id(server_id)
    if not server:
        flash('Сервер не найден', 'error')
        return redirect(url_for('admin_servers'))
    
    try:
        if server_manager.delete_server(server_id):
            flash(f'Сервер "{server["name"]}" удален!', 'success')
            logging.info(f"Удален сервер: {server['name']} ({server['ip']})")
        else:
            flash('Ошибка удаления сервера', 'error')
    except Exception as e:
        flash(f'Ошибка удаления сервера: {e}', 'error')
    
    return redirect(url_for('admin_servers'))

@app.route('/admin')
def admin():
    """Страница входа в админку"""
    if 'admin_logged_in' in session:
        servers_data = update_servers_list()
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

# Функция для проверки и предложения установки зависимостей
def check_dependencies():
    """Проверка зависимостей и предложение автоустановки"""
    missing_critical = []
    missing_optional = []
    
    # Проверяем критические зависимости
    try:
        import flask
    except ImportError:
        missing_critical.append('flask')
    
    # Проверяем опциональные зависимости
    try:
        import psutil
    except ImportError:
        missing_optional.append('psutil')
    
    try:
        import cpuinfo
    except ImportError:
        missing_optional.append('py-cpuinfo')
    
    # Если отсутствуют критические зависимости - останавливаем
    if missing_critical:
        print("❌ ОТСУТСТВУЮТ КРИТИЧЕСКИЕ ЗАВИСИМОСТИ:")
        for module in missing_critical:
            print(f"   - {module}")
        print("\n🔧 Для автоматической установки запустите:")
        print("   python auto_install.py")
        return False
    
    # Если отсутствуют только опциональные - предупреждаем но продолжаем
    if missing_optional:
        print("⚠️ ОТСУТСТВУЮТ ОПЦИОНАЛЬНЫЕ ЗАВИСИМОСТИ:")
        for module in missing_optional:
            print(f"   - {module}")
        print("\n📋 Приложение будет работать с ограниченной функциональностью")
        print("🔧 Для полной функциональности запустите: python auto_install.py")
        print("📦 Или установите вручную: pip install " + " ".join(missing_optional))
        print("\n⏳ Запуск через 3 секунды...")
        import time
        time.sleep(3)
    
    return True

# Замена deprecated @app.before_first_request на современный подход
app_initialized = False

@app.before_request
def initialize_app():
    """Инициализация приложения при первом запросе"""
    global app_initialized
    if not app_initialized:
        app_initialized = True
        # Проверяем зависимости при первом запросе
        if not check_dependencies():
            return jsonify({
                'error': 'Отсутствуют зависимости',
                'solution': 'Запустите: python auto_install.py'
            }), 500
        
        # Инициализируем список серверов с локальной машиной
        update_servers_list()
        logging.info("Приложение инициализировано")

# Обработчики ошибок
@app.errorhandler(404)
def not_found(error):
    # Проверяем если это API запрос
    if request.path.startswith('/api'):
        return jsonify({'ошибка': 'Страница не найдена'}), 404
    # Для обычных страниц возвращаем HTML
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    if request.path.startswith('/api'):
        return jsonify({'ошибка': 'Внутренняя ошибка сервера'}), 500
    return render_template('500.html'), 500

@app.route('/api/sync-database')
def sync_database():
    """API для синхронизации с базой данных"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    if not DATABASE_AVAILABLE:
        return jsonify({'error': 'База данных недоступна'}), 500
    
    try:
        # Получаем статистику
        servers = db_manager.get_all_servers()
        stats = {
            'servers_count': len(servers),
            'database_available': DATABASE_AVAILABLE,
            'last_sync': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return jsonify({
            'status': 'success',
            'message': 'Синхронизация выполнена',
            'stats': stats
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/admin/database')
def admin_database():
    """Страница управления базой данных"""
    if 'admin_logged_in' not in session:
        return redirect(url_for('admin'))
    
    stats = {}
    if DATABASE_AVAILABLE:
        try:
            servers = db_manager.get_all_servers()
            alerts = db_manager.get_active_alerts()
            
            stats = {
                'database_available': True,
                'servers_count': len(servers),
                'active_alerts': len(alerts),
                'database_file': db_manager.db_path,
                'file_size': os.path.getsize(db_manager.db_path) if os.path.exists(db_manager.db_path) else 0
            }
        except Exception as e:
            stats = {'database_available': False, 'error': str(e)}
    else:
        stats = {'database_available': False, 'error': 'База данных недоступна'}
    
    return render_template('admin_database.html', stats=stats)

@app.route('/admin/servers/<int:server_id>/test-ssh')
def admin_test_ssh(server_id):
    """Тестирование SSH подключения"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    if not SSH_MONITOR_AVAILABLE:
        return jsonify({'error': 'SSH мониторинг недоступен'}), 500
    
    server = server_manager.get_server_by_id(server_id)
    if not server:
        return jsonify({'error': 'Сервер не найден'}), 404
    
    result = ssh_monitor.test_ssh_connection(
        host=server['ip'],
        port=server.get('port', 22),
        username=server.get('username', 'root'),
        key_path=server.get('key_path'),
        password=server.get('password')
    )
    
    return jsonify(result)

@app.route('/admin/servers/<int:server_id>/get-metrics')
def admin_get_ssh_metrics(server_id):
    """Получение метрик через SSH"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    if not SSH_MONITOR_AVAILABLE:
        return jsonify({'error': 'SSH мониторинг недоступен'}), 500
    
    server = server_manager.get_server_by_id(server_id)
    if not server:
        return jsonify({'error': 'Сервер не найден'}), 404
    
    metrics = ssh_monitor.get_server_metrics(
        host=server['ip'],
        port=server.get('port', 22),
        username=server.get('username', 'root'),
        key_path=server.get('key_path'),
        password=server.get('password')
    )
    
    # Обновляем метрики в базе
    if metrics.get('ssh_success'):
        server_manager.update_server_metrics(server_id, metrics)
        return jsonify({
            'success': True,
            'message': 'Метрики получены и обновлены',
            'metrics': metrics
        })
    else:
        return jsonify({
            'success': False,
            'error': metrics.get('error', 'Неизвестная ошибка'),
            'metrics': metrics
        })

@app.route('/admin/monitoring-status')
def admin_monitoring_status():
    """Статус SSH мониторинга"""
    if 'admin_logged_in' not in session:
        return jsonify({'error': 'Требуется авторизация'}), 401
    
    if not SSH_MONITOR_AVAILABLE:
        return jsonify({'ssh_available': False, 'error': 'SSH мониторинг недоступен'})
    
    status = ssh_monitor.get_monitoring_status()
    return jsonify(status)

if __name__ == '__main__':
    # Проверяем зависимости перед запуском
    if not check_dependencies():
        print("\n🛑 Запуск невозможен без критических зависимостей")
        sys.exit(1)
    
    logging.info("Запуск системы мониторинга")
    
    # Получаем параметры запуска
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", 5001))
    debug = os.environ.get("FLASK_DEBUG", "False").lower() == "true"
    
    print(f"🚀 Запуск приложения мониторинга на {host}:{port}")
    print(f"🌐 Откройте браузер: http://{host}:{port}")
    print("📊 Доступные разделы:")
    print("   / - Главная страница")
    print("   /servers - Мониторинг серверов")
    print("   /system - Системный мониторинг")
    print("   /admin - Админка (admin/admin123)")
    
    app.run(host=host, port=port, debug=debug)
