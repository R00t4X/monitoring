from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()

class Server(db.Model):
    __tablename__ = 'servers'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    hostname = db.Column(db.String(255), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    port = db.Column(db.Integer, default=22)
    ssh_username = db.Column(db.String(50))
    ssh_key_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='unknown')
    os_type = db.Column(db.String(50))
    location = db.Column(db.String(100))
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_check = db.Column(db.DateTime)
    
    # Relationships
    metrics = db.relationship('ServerMetric', backref='server', lazy=True, cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='server', lazy=True)

class ServerMetric(db.Model):
    __tablename__ = 'server_metrics'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    # CPU Metrics
    cpu_usage = db.Column(db.Float)
    cpu_count = db.Column(db.Integer)
    cpu_frequency = db.Column(db.Float)
    load_avg_1 = db.Column(db.Float)
    load_avg_5 = db.Column(db.Float)
    load_avg_15 = db.Column(db.Float)
    
    # Memory Metrics
    memory_total = db.Column(db.BigInteger)
    memory_used = db.Column(db.BigInteger)
    memory_available = db.Column(db.BigInteger)
    memory_percent = db.Column(db.Float)
    swap_total = db.Column(db.BigInteger)
    swap_used = db.Column(db.BigInteger)
    swap_percent = db.Column(db.Float)
    
    # Disk Metrics
    disk_usage = db.Column(db.Text)  # JSON данные о всех дисках
    disk_io_read = db.Column(db.BigInteger)
    disk_io_write = db.Column(db.BigInteger)
    
    # Network Metrics
    network_bytes_sent = db.Column(db.BigInteger)
    network_bytes_recv = db.Column(db.BigInteger)
    network_packets_sent = db.Column(db.BigInteger)
    network_packets_recv = db.Column(db.BigInteger)
    
    # Process Metrics
    process_count = db.Column(db.Integer)
    
    # Temperature (if available)
    temperature = db.Column(db.Text)  # JSON данные о температуре
    
    def to_dict(self):
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_usage': self.cpu_usage,
            'memory_percent': self.memory_percent,
            'disk_usage': json.loads(self.disk_usage) if self.disk_usage else [],
            'network_bytes_sent': self.network_bytes_sent,
            'network_bytes_recv': self.network_bytes_recv,
        }

class Alert(db.Model):
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'), nullable=False)
    alert_type = db.Column(db.String(50), nullable=False)  # cpu, memory, disk, network, custom
    severity = db.Column(db.String(20), nullable=False)  # low, medium, high, critical
    message = db.Column(db.Text, nullable=False)
    threshold_value = db.Column(db.Float)
    current_value = db.Column(db.Float)
    is_resolved = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    resolved_at = db.Column(db.DateTime)
    
    def to_dict(self):
        return {
            'id': self.id,
            'server_id': self.server_id,
            'server_name': self.server.name if self.server else 'Unknown',
            'alert_type': self.alert_type,
            'severity': self.severity,
            'message': self.message,
            'threshold_value': self.threshold_value,
            'current_value': self.current_value,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }

class MonitoringConfig(db.Model):
    __tablename__ = 'monitoring_config'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text)
    description = db.Column(db.Text)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='operator')  # admin, operator, viewer
    is_active = db.Column(db.Boolean, default=True)
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
