"""
Управление серверами для мониторинга.
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

# Импортируем менеджер базы данных
try:
    from database import db_manager
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

class ServerManager:
    def __init__(self, data_file='servers_data.json'):
        self.data_file = data_file
        self.servers = []
        
        # Используем базу данных если доступна
        if DATABASE_AVAILABLE:
            self.use_database = True
            self.load_servers_from_db()
        else:
            self.use_database = False
            self.load_servers()
    
    def load_servers_from_db(self):
        """Загрузка серверов из базы данных"""
        if DATABASE_AVAILABLE:
            self.servers = db_manager.get_all_servers()
        else:
            self.servers = []
    
    def load_servers(self):
        """Загрузка серверов из файла"""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.servers = json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Ошибка загрузки серверов: {e}")
                self.servers = []
        else:
            # Создаем базовые серверы если файл не существует
            self.create_default_servers()
    
    def save_servers(self):
        """Сохранение серверов в файл"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.servers, f, ensure_ascii=False, indent=2)
        except IOError as e:
            print(f"Ошибка сохранения серверов: {e}")
    
    def create_default_servers(self):
        """Создание серверов по умолчанию"""
        self.servers = [
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
                'description': 'Основной веб-сервер',
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
                'description': 'Сервер базы данных MySQL',
                'alerts': ['Высокое использование CPU', 'Высокое использование памяти']
            }
        ]
        self.save_servers()
    
    def get_all_servers(self) -> List[Dict]:
        """Получение всех серверов"""
        if self.use_database and DATABASE_AVAILABLE:
            return db_manager.get_all_servers()
        return self.servers
    
    def get_server_by_id(self, server_id: int) -> Optional[Dict]:
        """Получение сервера по ID"""
        if self.use_database and DATABASE_AVAILABLE:
            return db_manager.get_server_by_id(server_id)
        
        for server in self.servers:
            if server.get('id') == server_id:
                return server
        return None
    
    def add_server(self, server_data: Dict) -> Dict:
        """Добавление нового сервера"""
        if self.use_database and DATABASE_AVAILABLE:
            return db_manager.add_server(server_data)
        
        # Fallback к JSON файлу
        max_id = max([s.get('id', 0) for s in self.servers], default=0)
        server_data['id'] = max_id + 1
        
        # Устанавливаем значения по умолчанию
        server_data.setdefault('status', 'unknown')
        server_data.setdefault('cpu', 0)
        server_data.setdefault('memory', 0)
        server_data.setdefault('disk', 0)
        server_data.setdefault('network_in', 0)
        server_data.setdefault('network_out', 0)
        server_data.setdefault('uptime', '0 дней 0 часов')
        server_data.setdefault('alerts', [])
        server_data['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.servers.append(server_data)
        self.save_servers()
        return server_data
    
    def update_server(self, server_id: int, server_data: Dict) -> bool:
        """Обновление сервера"""
        if self.use_database and DATABASE_AVAILABLE:
            return db_manager.update_server(server_id, server_data)
        
        # Fallback к JSON файлу
        for i, server in enumerate(self.servers):
            if server.get('id') == server_id:
                server_data['id'] = server_id
                server_data['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                # Сохраняем метрики если они не переданы
                for metric in ['cpu', 'memory', 'disk', 'network_in', 'network_out', 'uptime', 'alerts']:
                    if metric not in server_data:
                        server_data[metric] = server.get(metric, 0 if metric != 'alerts' else [])
                
                self.servers[i] = server_data
                self.save_servers()
                return True
        return False
    
    def delete_server(self, server_id: int) -> bool:
        """Удаление сервера"""
        if self.use_database and DATABASE_AVAILABLE:
            return db_manager.delete_server(server_id)
        
        # Fallback к JSON файлу
        for i, server in enumerate(self.servers):
            if server.get('id') == server_id:
                del self.servers[i]
                self.save_servers()
                return True
        return False
    
    def update_server_metrics(self, server_id: int, metrics: Dict) -> bool:
        """Обновление метрик сервера"""
        if self.use_database and DATABASE_AVAILABLE:
            return db_manager.update_server_metrics(server_id, metrics)
        
        # Fallback логика
        server = self.get_server_by_id(server_id)
        if server:
            server.update(metrics)
            server['last_check'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.save_servers()
            return True
        return False
    
    def get_server_statistics(self) -> Dict:
        """Получение статистики серверов"""
        servers = self.get_all_servers()
        
        stats = {
            'total': len(servers),
            'online': len([s for s in servers if s.get('status') == 'online']),
            'offline': len([s for s in servers if s.get('status') == 'offline']),
            'warning': len([s for s in servers if s.get('status') == 'warning']),
            'avg_cpu': sum(s.get('cpu', 0) for s in servers) / len(servers) if servers else 0,
            'avg_memory': sum(s.get('memory', 0) for s in servers) / len(servers) if servers else 0,
            'avg_disk': sum(s.get('disk', 0) for s in servers) / len(servers) if servers else 0
        }
        
        return stats

# Глобальный экземпляр менеджера серверов
server_manager = ServerManager()
