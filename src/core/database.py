"""
Управление базой данных.
"""
import sqlite3
import os
from datetime import datetime

class DatabaseManager:
    def __init__(self):
        self.db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'data', 'monitoring.db')
        self._init_db()
    
    def _init_db(self):
        """Инициализация базы данных"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS servers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    ip TEXT NOT NULL,
                    port INTEGER DEFAULT 22,
                    username TEXT DEFAULT 'root',
                    description TEXT,
                    status TEXT DEFAULT 'unknown',
                    last_check TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    server_id INTEGER,
                    cpu_percent REAL,
                    memory_percent REAL,
                    disk_percent REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (server_id) REFERENCES servers (id)
                )
            ''')
            conn.commit()
    
    def get_all_servers(self):
        """Получение всех серверов"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM servers ORDER BY id')
            return [dict(row) for row in cursor.fetchall()]
    
    def add_server(self, server_data):
        """Добавление сервера"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                INSERT INTO servers (name, ip, port, username, description)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                server_data['name'],
                server_data['ip'],
                server_data['port'],
                server_data['username'],
                server_data['description']
            ))
            conn.commit()
            return cursor.lastrowid
    
    def get_server(self, server_id):
        """Получение сервера по ID"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('SELECT * FROM servers WHERE id = ?', (server_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def update_server(self, server_id, data):
        """Обновление сервера"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE servers 
                SET name=?, ip=?, port=?, username=?, description=?
                WHERE id=?
            ''', (data['name'], data['ip'], data['port'], data['username'], data['description'], server_id))
            conn.commit()
    
    def delete_server(self, server_id):
        """Удаление сервера"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM servers WHERE id = ?', (server_id,))
            conn.commit()
    
    def update_server_status(self, server_id, status, metrics=None):
        """Обновление статуса и метрик сервера"""
        with sqlite3.connect(self.db_path) as conn:
            if metrics:
                conn.execute('''
                    UPDATE servers 
                    SET status=?, last_check=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (status, server_id))
                
                # Сохраняем метрики
                conn.execute('''
                    INSERT INTO metrics (server_id, cpu_percent, memory_percent, disk_percent)
                    VALUES (?, ?, ?, ?)
                ''', (server_id, metrics.get('cpu', 0), metrics.get('memory', 0), metrics.get('disk', 0)))
            else:
                conn.execute('''
                    UPDATE servers 
                    SET status=?, last_check=CURRENT_TIMESTAMP
                    WHERE id=?
                ''', (status, server_id))
            conn.commit()
    
    def get_server_metrics(self, server_id, limit=100):
        """Получение истории метрик сервера"""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute('''
                SELECT * FROM metrics 
                WHERE server_id = ? 
                ORDER BY timestamp DESC 
                LIMIT ?
            ''', (server_id, limit))
            return [dict(row) for row in cursor.fetchall()]
    
    def cleanup_old_metrics(self, days=30):
        """Очистка старых метрик"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                DELETE FROM metrics 
                WHERE timestamp < datetime('now', '-{} days')
            '''.format(days))
            conn.commit()
