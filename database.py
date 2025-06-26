"""
Управление базой данных для системы мониторинга.
"""
import sqlite3
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

class DatabaseManager:
    def __init__(self, db_path='monitoring.db'):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Инициализация базы данных и создание таблиц"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    port INTEGER DEFAULT 22,
                    location TEXT,
                    os TEXT,
                    description TEXT,
                    status TEXT DEFAULT 'unknown',
                    cpu REAL DEFAULT 0,
                    memory REAL DEFAULT 0,
                    disk REAL DEFAULT 0,
                    network_in REAL DEFAULT 0,
                    network_out REAL DEFAULT 0,
                    uptime TEXT DEFAULT '0 дней 0 часов',
                    alerts TEXT DEFAULT '[]',
                    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    data TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES servers (id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS alerts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER,
                    alert_type TEXT NOT NULL,
                    message TEXT NOT NULL,
                    severity TEXT DEFAULT 'warning',
                    is_resolved BOOLEAN DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES servers (id)
                )
            ''')
            
            # Создаем индексы для производительности
            conn.execute('CREATE INDEX IF NOT EXISTS idx_servers_status ON servers(status)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_metrics_server_timestamp ON metrics(server_id, timestamp)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_alerts_server ON alerts(server_id, is_resolved)')
            
            conn.commit()
    
    # Управление серверами
    def get_all_servers(self) -> List[Dict]:
        """Получение всех серверов"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM servers ORDER BY id
            ''')
            servers = []
            for row in cursor.fetchall():
                server = dict(row)
                server['alerts'] = json.loads(server['alerts'] or '[]')
                servers.append(server)
            return servers
    
    def get_server_by_id(self, server_id: int) -> Optional[Dict]:
        """Получение сервера по ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM servers WHERE id = ?', (server_id,))
            row = cursor.fetchone()
            if row:
                server = dict(row)
                server['alerts'] = json.loads(server['alerts'] or '[]')
                return server
        return None
    
    def add_server(self, server_data: Dict) -> Dict:
        """Добавление нового сервера"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO servers (name, ip, port, location, os, description)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                server_data.get('name'),
                server_data.get('ip'),
                server_data.get('port', 22),
                server_data.get('location', ''),
                server_data.get('os', ''),
                server_data.get('description', '')
            ))
            server_id = cursor.lastrowid
            conn.commit()
            
            return self.get_server_by_id(server_id)
    
    def update_server(self, server_id: int, server_data: Dict) -> bool:
        """Обновление сервера"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                UPDATE servers 
                SET name=?, ip=?, port=?, location=?, os=?, description=?, last_check=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (
                server_data.get('name'),
                server_data.get('ip'),
                server_data.get('port', 22),
                server_data.get('location', ''),
                server_data.get('os', ''),
                server_data.get('description', ''),
                server_id
            ))
            conn.commit()
            return cursor.rowcount > 0
    
    def delete_server(self, server_id: int) -> bool:
        """Удаление сервера"""
        with sqlite3.connect(self.db_path) as conn:
            # Удаляем связанные метрики и алерты
            conn.execute('DELETE FROM metrics WHERE server_id = ?', (server_id,))
            conn.execute('DELETE FROM alerts WHERE server_id = ?', (server_id,))
            
            # Удаляем сервер
            cursor = conn.execute('DELETE FROM servers WHERE id = ?', (server_id,))
            conn.commit()
            return cursor.rowcount > 0
    
    def update_server_metrics(self, server_id: int, metrics: Dict) -> bool:
        """Обновление метрик сервера"""
        with sqlite3.connect(self.db_path) as conn:
            # Обновляем основные метрики в таблице серверов
            conn.execute('''
                UPDATE servers 
                SET cpu=?, memory=?, disk=?, network_in=?, network_out=?, 
                    uptime=?, status=?, last_check=CURRENT_TIMESTAMP
                WHERE id=?
            ''', (
                metrics.get('cpu', 0),
                metrics.get('memory', 0),
                metrics.get('disk', 0),
                metrics.get('network_in', 0),
                metrics.get('network_out', 0),
                metrics.get('uptime', ''),
                metrics.get('status', 'unknown'),
                server_id
            ))
            
            # Сохраняем детальные метрики
            for metric_type, value in metrics.items():
                if metric_type in ['cpu', 'memory', 'disk']:
                    conn.execute('''
                        INSERT INTO metrics (server_id, metric_type, value, data)
                        VALUES (?, ?, ?, ?)
                    ''', (server_id, metric_type, value, json.dumps(metrics)))
            
            conn.commit()
            return True
    
    # Управление метриками
    def get_server_metrics(self, server_id: int, metric_type: str = None, limit: int = 100) -> List[Dict]:
        """Получение метрик сервера"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = 'SELECT * FROM metrics WHERE server_id = ?'
            params = [server_id]
            
            if metric_type:
                query += ' AND metric_type = ?'
                params.append(metric_type)
            
            query += ' ORDER BY timestamp DESC LIMIT ?'
            params.append(limit)
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_metrics(self, days: int = 30):
        """Очистка старых метрик"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                DELETE FROM metrics 
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))
            conn.commit()
    
    # Управление алертами
    def add_alert(self, server_id: int, alert_type: str, message: str, severity: str = 'warning') -> int:
        """Добавление алерта"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO alerts (server_id, alert_type, message, severity)
                VALUES (?, ?, ?, ?)
            ''', (server_id, alert_type, message, severity))
            conn.commit()
            return cursor.lastrowid
    
    def get_active_alerts(self, server_id: int = None) -> List[Dict]:
        """Получение активных алертов"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            query = 'SELECT * FROM alerts WHERE is_resolved = 0'
            params = []
            
            if server_id:
                query += ' AND server_id = ?'
                params.append(server_id)
            
            query += ' ORDER BY created_at DESC'
            
            cursor = conn.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]
    
    def resolve_alert(self, alert_id: int) -> bool:
        """Разрешение алерта"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                UPDATE alerts 
                SET is_resolved = 1, resolved_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (alert_id,))
            conn.commit()
            return cursor.rowcount > 0

# Глобальный экземпляр менеджера базы данных
db_manager = DatabaseManager()
