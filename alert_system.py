import smtplib
import json
import requests
import logging
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

class AlertSeverity(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertType(Enum):
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    TEMPERATURE = "temperature"
    PROCESS = "process"
    CUSTOM = "custom"

@dataclass
class AlertRule:
    id: str
    name: str
    alert_type: AlertType
    metric_path: str  # e.g., "cpu.usage_total"
    condition: str    # "greater_than", "less_than", "equals"
    threshold: float
    severity: AlertSeverity
    duration_minutes: int = 5  # Alert only if condition persists
    enabled: bool = True
    description: str = ""
    
    def check_condition(self, value: float) -> bool:
        """Проверка условия срабатывания"""
        if self.condition == "greater_than":
            return value > self.threshold
        elif self.condition == "less_than":
            return value < self.threshold
        elif self.condition == "equals":
            return abs(value - self.threshold) < 0.01
        return False

@dataclass
class Alert:
    id: str
    rule_id: str
    server_id: Optional[str]
    message: str
    severity: AlertSeverity
    alert_type: AlertType
    current_value: float
    threshold_value: float
    created_at: datetime
    resolved_at: Optional[datetime] = None
    is_resolved: bool = False
    
    def to_dict(self) -> Dict:
        return {
            'id': self.id,
            'rule_id': self.rule_id,
            'server_id': self.server_id,
            'message': self.message,
            'severity': self.severity.value,
            'alert_type': self.alert_type.value,
            'current_value': self.current_value,
            'threshold_value': self.threshold_value,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'is_resolved': self.is_resolved
        }

class AlertNotifier:
    """Базовый класс для отправки уведомлений"""
    
    def send_alert(self, alert: Alert) -> bool:
        raise NotImplementedError

class EmailNotifier(AlertNotifier):
    def __init__(self, smtp_server: str, smtp_port: int, username: str, 
                 password: str, from_email: str, to_emails: List[str]):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.username = username
        self.password = password
        self.from_email = from_email
        self.to_emails = to_emails
    
    def send_alert(self, alert: Alert) -> bool:
        try:
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.value.upper()}] Monitoring Alert - {alert.alert_type.value}"
            
            body = f"""
            Alert Details:
            
            Server: {alert.server_id or 'Local System'}
            Type: {alert.alert_type.value}
            Severity: {alert.severity.value}
            Message: {alert.message}
            
            Current Value: {alert.current_value}
            Threshold: {alert.threshold_value}
            
            Time: {alert.created_at.strftime('%Y-%m-%d %H:%M:%S')}
            
            Please check your monitoring dashboard for more details.
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.username, self.password)
            server.send_message(msg)
            server.quit()
            
            logging.info(f"Email alert sent for {alert.id}")
            return True
            
        except Exception as e:
            logging.error(f"Failed to send email alert: {e}")
            return False

class WebhookNotifier(AlertNotifier):
    def __init__(self, webhook_url: str, headers: Dict[str, str] = None):
        self.webhook_url = webhook_url
        self.headers = headers or {'Content-Type': 'application/json'}
    
    def send_alert(self, alert: Alert) -> bool:
        try:
            payload = {
                'alert': alert.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
            
            response = requests.post(
                self.webhook_url,
                json=payload,
                headers=self.headers,
                timeout=10
            )
            
            if response.status_code == 200:
                logging.info(f"Webhook alert sent for {alert.id}")
                return True
            else:
                logging.error(f"Webhook failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to send webhook alert: {e}")
            return False

class SlackNotifier(AlertNotifier):
    def __init__(self, webhook_url: str):
        self.webhook_url = webhook_url
    
    def send_alert(self, alert: Alert) -> bool:
        try:
            severity_colors = {
                AlertSeverity.LOW: "#36a64f",
                AlertSeverity.MEDIUM: "#ff9900",
                AlertSeverity.HIGH: "#ff6600",
                AlertSeverity.CRITICAL: "#ff0000"
            }
            
            payload = {
                "attachments": [{
                    "color": severity_colors.get(alert.severity, "#cccccc"),
                    "title": f"Monitoring Alert - {alert.alert_type.value.title()}",
                    "text": alert.message,
                    "fields": [
                        {"title": "Server", "value": alert.server_id or "Local System", "short": True},
                        {"title": "Severity", "value": alert.severity.value.upper(), "short": True},
                        {"title": "Current Value", "value": str(alert.current_value), "short": True},
                        {"title": "Threshold", "value": str(alert.threshold_value), "short": True}
                    ],
                    "footer": "Monitoring System",
                    "ts": int(alert.created_at.timestamp())
                }]
            }
            
            response = requests.post(self.webhook_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logging.info(f"Slack alert sent for {alert.id}")
                return True
            else:
                logging.error(f"Slack webhook failed with status {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Failed to send Slack alert: {e}")
            return False

class AlertManager:
    def __init__(self):
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notifiers: List[AlertNotifier] = []
        self.rule_states: Dict[str, Dict] = {}  # Для отслеживания состояний правил
        
        # Загружаем стандартные правила
        self._load_default_rules()
    
    def _load_default_rules(self):
        """Загрузка стандартных правил мониторинга"""
        default_rules = [
            AlertRule(
                id="cpu_high",
                name="High CPU Usage",
                alert_type=AlertType.CPU,
                metric_path="cpu.usage_total",
                condition="greater_than",
                threshold=80.0,
                severity=AlertSeverity.HIGH,
                duration_minutes=5,
                description="CPU usage is too high"
            ),
            AlertRule(
                id="cpu_critical",
                name="Critical CPU Usage",
                alert_type=AlertType.CPU,
                metric_path="cpu.usage_total",
                condition="greater_than",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                duration_minutes=2,
                description="CPU usage is critically high"
            ),
            AlertRule(
                id="memory_high",
                name="High Memory Usage",
                alert_type=AlertType.MEMORY,
                metric_path="memory.percent",
                condition="greater_than",
                threshold=85.0,
                severity=AlertSeverity.HIGH,
                duration_minutes=5,
                description="Memory usage is too high"
            ),
            AlertRule(
                id="memory_critical",
                name="Critical Memory Usage",
                alert_type=AlertType.MEMORY,
                metric_path="memory.percent",
                condition="greater_than",
                threshold=95.0,
                severity=AlertSeverity.CRITICAL,
                duration_minutes=2,
                description="Memory usage is critically high"
            ),
            AlertRule(
                id="disk_high",
                name="High Disk Usage",
                alert_type=AlertType.DISK,
                metric_path="disk.partitions.0.percent",
                condition="greater_than",
                threshold=90.0,
                severity=AlertSeverity.HIGH,
                duration_minutes=10,
                description="Disk usage is too high"
            )
        ]
        
        for rule in default_rules:
            self.add_rule(rule)
    
    def add_rule(self, rule: AlertRule):
        """Добавление правила мониторинга"""
        self.rules[rule.id] = rule
        self.rule_states[rule.id] = {
            'triggered_at': None,
            'last_check': None,
            'consecutive_violations': 0
        }
        logging.info(f"Added alert rule: {rule.name}")
    
    def remove_rule(self, rule_id: str):
        """Удаление правила мониторинга"""
        if rule_id in self.rules:
            del self.rules[rule_id]
            del self.rule_states[rule_id]
            logging.info(f"Removed alert rule: {rule_id}")
    
    def add_notifier(self, notifier: AlertNotifier):
        """Добавление способа уведомлений"""
        self.notifiers.append(notifier)
    
    def check_metrics(self, metrics: Dict, server_id: str = None):
        """Проверка метрик на соответствие правилам"""
        current_time = datetime.now()
        
        for rule_id, rule in self.rules.items():
            if not rule.enabled:
                continue
            
            try:
                # Извлекаем значение по пути
                value = self._get_value_by_path(metrics, rule.metric_path)
                if value is None:
                    continue
                
                # Проверяем условие
                violation = rule.check_condition(value)
                state = self.rule_states[rule_id]
                
                if violation:
                    if state['triggered_at'] is None:
                        state['triggered_at'] = current_time
                        state['consecutive_violations'] = 1
                    else:
                        state['consecutive_violations'] += 1
                        
                        # Проверяем, нужно ли создать алерт
                        duration = current_time - state['triggered_at']
                        if duration.total_seconds() >= rule.duration_minutes * 60:
                            self._create_alert(rule, value, server_id)
                else:
                    # Условие не выполняется - сбрасываем состояние
                    if state['triggered_at'] is not None:
                        # Возможно, нужно закрыть активный алерт
                        self._resolve_alert(rule_id)
                    
                    state['triggered_at'] = None
                    state['consecutive_violations'] = 0
                
                state['last_check'] = current_time
                
            except Exception as e:
                logging.error(f"Error checking rule {rule_id}: {e}")
    
    def _get_value_by_path(self, data: Dict, path: str):
        """Извлечение значения по пути (например, 'cpu.usage_total')"""
        try:
            keys = path.split('.')
            value = data
            
            for key in keys:
                if key.isdigit():
                    # Индекс массива
                    value = value[int(key)]
                else:
                    value = value[key]
            
            return float(value) if value is not None else None
            
        except (KeyError, IndexError, TypeError, ValueError):
            return None
    
    def _create_alert(self, rule: AlertRule, current_value: float, server_id: str = None):
        """Создание нового алерта"""
        alert_id = f"{rule.id}_{server_id or 'local'}_{int(datetime.now().timestamp())}"
        
        # Проверяем, нет ли уже активного алерта для этого правила
        existing_alert_key = f"{rule.id}_{server_id or 'local'}"
        if existing_alert_key in self.active_alerts:
            return  # Алерт уже существует
        
        alert = Alert(
            id=alert_id,
            rule_id=rule.id,
            server_id=server_id,
            message=f"{rule.description}: {current_value:.2f} (threshold: {rule.threshold})",
            severity=rule.severity,
            alert_type=rule.alert_type,
            current_value=current_value,
            threshold_value=rule.threshold,
            created_at=datetime.now()
        )
        
        self.active_alerts[existing_alert_key] = alert
        self.alert_history.append(alert)
        
        # Отправляем уведомления
        self._send_notifications(alert)
        
        logging.warning(f"Alert created: {alert.message}")
    
    def _resolve_alert(self, rule_id: str, server_id: str = None):
        """Разрешение алерта"""
        alert_key = f"{rule_id}_{server_id or 'local'}"
        
        if alert_key in self.active_alerts:
            alert = self.active_alerts[alert_key]
            alert.is_resolved = True
            alert.resolved_at = datetime.now()
            
            del self.active_alerts[alert_key]
            logging.info(f"Alert resolved: {alert.id}")
    
    def _send_notifications(self, alert: Alert):
        """Отправка уведомлений через все настроенные каналы"""
        for notifier in self.notifiers:
            try:
                notifier.send_alert(alert)
            except Exception as e:
                logging.error(f"Failed to send notification via {type(notifier).__name__}: {e}")
    
    def get_active_alerts(self) -> List[Alert]:
        """Получение списка активных алертов"""
        return list(self.active_alerts.values())
    
    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Получение истории алертов"""
        return self.alert_history[-limit:]
    
    def get_alert_stats(self) -> Dict:
        """Получение статистики по алертам"""
        total_alerts = len(self.alert_history)
        active_count = len(self.active_alerts)
        
        severity_counts = {}
        type_counts = {}
        
        for alert in self.alert_history:
            severity_counts[alert.severity.value] = severity_counts.get(alert.severity.value, 0) + 1
            type_counts[alert.alert_type.value] = type_counts.get(alert.alert_type.value, 0) + 1
        
        return {
            'total_alerts': total_alerts,
            'active_alerts': active_count,
            'resolved_alerts': total_alerts - active_count,
            'alerts_by_severity': severity_counts,
            'alerts_by_type': type_counts,
            'rules_count': len(self.rules),
            'enabled_rules': len([r for r in self.rules.values() if r.enabled])
        }

# Глобальный экземпляр менеджера алертов
alert_manager = AlertManager()
