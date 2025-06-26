"""
Модели для серверов и метрик мониторинга.
"""
import json
import datetime
from app import db

class Server(db.Model):
    """Модель сервера для мониторинга."""
    __tablename__ = 'servers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hostname = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    port = db.Column(db.Integer, default=22)
    
    # Данные для подключения
    connection_type = db.Column(db.String(20), default='ssh')  # ssh, agent, snmp
    username = db.Column(db.String(50))
    auth_method = db.Column(db.String(20), default='key')  # key, password
    auth_key = db.Column(db.Text)  # path to key or hashed password
    
    # Информация о сервере
    os_type = db.Column(db.String(50))
    location = db.Column(db.String(100))
    description = db.Column(db.Text)
    
    # Статус
    status = db.Column(db.String(20), default='unknown')  # online, offline, warning, error
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    last_check = db.Column(db.DateTime)
    
    # Связи
    metrics = db.relationship('ServerMetric', backref='server', lazy='dynamic',
                              cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='server', lazy='dynamic')
    
    def to_dict(self):
        """Преобразование в словарь для API."""
        return {
            'id': self.id,
            'name': self.name,
            'hostname': self.hostname,
            'ip_address': self.ip_address,
            'port': self.port,
            'status': self.status,
            'os_type': self.os_type,
            'location': self.location,
            'is_active': self.is_active,
            'last_check': self.last_check.isoformat() if self.last_check else None
        }
    
    def __repr__(self):
        return f'<Server {self.name} ({self.ip_address})>'

class ServerMetric(db.Model):
    """Метрики сервера."""
    __tablename__ = 'server_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow, index=True)
    metric_type = db.Column(db.String(20), nullable=False)  # cpu, memory, disk, network, etc.
    
    # Данные метрик в формате JSON
    data = db.Column(db.Text, nullable=False)  # JSON string
    
    @property
    def metric_data(self):
        """Получение данных метрики в виде словаря."""
        return json.loads(self.data)
    
    @metric_data.setter
    def metric_data(self, value):
        """Сохранение данных метрики."""
        self.data = json.dumps(value)
    
    def __repr__(self):
        return f'<ServerMetric {self.server_id} {self.metric_type} {self.timestamp}>'

class MetricDefinition(db.Model):
    """Определение метрик и их параметров."""
    __tablename__ = 'metric_definitions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    display_name = db.Column(db.String(100))
    category = db.Column(db.String(50))  # cpu, memory, disk, network
    unit = db.Column(db.String(20))  # %, MB, GB/s, etc.
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    
    # Параметры отображения
    display_order = db.Column(db.Integer, default=0)
    chart_type = db.Column(db.String(20), default='line')  # line, bar, gauge
    chart_color = db.Column(db.String(20))
    
    # Пороговые значения для алертов
    warning_threshold = db.Column(db.Float)
    critical_threshold = db.Column(db.Float)
    
    def __repr__(self):
        return f'<MetricDefinition {self.name}>'
