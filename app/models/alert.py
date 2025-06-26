"""
Модели для системы оповещений.
"""
import datetime
from app import db

class AlertRule(db.Model):
    """Правило оповещения."""
    __tablename__ = 'alert_rules'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Тип и параметры правила
    metric_type = db.Column(db.String(50), nullable=False)  # cpu, memory, disk, etc.
    metric_path = db.Column(db.String(255), nullable=False)  # path to value in JSON data
    condition = db.Column(db.String(50), nullable=False)  # >, <, =, !=, etc.
    threshold = db.Column(db.Float, nullable=False)
    duration = db.Column(db.Integer, default=0)  # minutes, 0 for immediate alert
    
    # Уровень важности
    severity = db.Column(db.String(20), nullable=False, default='warning')  # info, warning, critical
    
    # Настройки
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow,
                           onupdate=datetime.datetime.utcnow)
    
    # Связи
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'))  # Null для глобальных правил
    notification_methods = db.relationship('NotificationMethod', secondary='alert_rule_notifications',
                                          backref=db.backref('alert_rules', lazy='dynamic'))
    
    def to_dict(self):
        """Преобразование в словарь для API."""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'metric_type': self.metric_type,
            'metric_path': self.metric_path,
            'condition': self.condition,
            'threshold': self.threshold,
            'duration': self.duration,
            'severity': self.severity,
            'is_active': self.is_active,
            'server_id': self.server_id
        }
    
    def __repr__(self):
        return f'<AlertRule {self.name}>'

class Alert(db.Model):
    """Конкретное оповещение."""
    __tablename__ = 'alerts'
    
    id = db.Column(db.Integer, primary_key=True)
    server_id = db.Column(db.Integer, db.ForeignKey('servers.id'))
    rule_id = db.Column(db.Integer, db.ForeignKey('alert_rules.id'))
    
    # Информация об оповещении
    message = db.Column(db.Text, nullable=False)
    severity = db.Column(db.String(20), nullable=False)
    current_value = db.Column(db.Float)
    threshold_value = db.Column(db.Float)
    
    # Статус
    is_acknowledged = db.Column(db.Boolean, default=False)
    is_resolved = db.Column(db.Boolean, default=False)
    
    # Временные метки
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    acknowledged_at = db.Column(db.DateTime)
    resolved_at = db.Column(db.DateTime)
    
    # Пользователь, который обработал алерт
    acknowledged_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Связи
    rule = db.relationship('AlertRule', backref='alerts')
    
    def to_dict(self):
        """Преобразование в словарь для API."""
        return {
            'id': self.id,
            'server_id': self.server_id,
            'server_name': self.server.name if self.server else None,
            'rule_id': self.rule_id,
            'rule_name': self.rule.name if self.rule else None,
            'message': self.message,
            'severity': self.severity,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'is_acknowledged': self.is_acknowledged,
            'is_resolved': self.is_resolved,
            'created_at': self.created_at.isoformat(),
            'acknowledged_at': self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        }
    
    def __repr__(self):
        return f'<Alert {self.id} {self.severity}>'

class NotificationMethod(db.Model):
    """Метод отправки оповещений."""
    __tablename__ = 'notification_methods'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(50), nullable=False)  # email, slack, webhook, etc.
    
    # Конфигурация в формате JSON
    config = db.Column(db.Text, nullable=False)  # JSON string
    
    # Настройки
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    def __repr__(self):
        return f'<NotificationMethod {self.name} ({self.type})>'

# Таблица связи между правилами и методами оповещений
alert_rule_notifications = db.Table(
    'alert_rule_notifications',
    db.Column('rule_id', db.Integer, db.ForeignKey('alert_rules.id'), primary_key=True),
    db.Column('method_id', db.Integer, db.ForeignKey('notification_methods.id'), primary_key=True)
)
