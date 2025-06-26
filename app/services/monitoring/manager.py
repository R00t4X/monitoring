"""
Управление мониторингом и координация работы различных мониторов.
"""
import os
import time
import logging
import threading
from typing import Dict, List, Optional
from datetime import datetime

from app import socketio, db
from app.models.server import Server, ServerMetric
from app.services.monitoring.system_monitor import SystemMonitor
from app.services.alerts.alert_manager import AlertManager

class MonitoringManager:
    """Управление процессами мониторинга."""
    
    def __init__(self):
        """Инициализация менеджера мониторинга."""
        self.logger = logging.getLogger('monitoring.manager')
        
        # Инициализация компонентов
        self.system_monitor = SystemMonitor()
        self.alert_manager = AlertManager()
        
        # Параметры мониторинга
        self.monitoring_interval = int(os.environ.get('MONITORING_INTERVAL', 30))
        self.is_running = False
        self.scheduler_thread = None
        
        # Настройка колбеков
        self.system_monitor.add_callback(self._handle_system_metrics)
    
    def start(self) -> None:
        """Запуск всех процессов мониторинга."""
        if self.is_running:
            self.logger.warning("Менеджер мониторинга уже запущен")
            return
        
        self.logger.info("Запуск менеджера мониторинга")
        
        # Запускаем мониторинг системы
        self.system_monitor.start_monitoring(interval=self.monitoring_interval)
        
        # Устанавливаем флаг работы
        self.is_running = True
        
        # Запускаем планировщик задач
        self.scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            daemon=True
        )
        self.scheduler_thread.start()
        
        self.logger.info("Менеджер мониторинга успешно запущен")
    
    def stop(self) -> None:
        """Остановка всех процессов мониторинга."""
        if not self.is_running:
            return
        
        self.logger.info("Остановка менеджера мониторинга")
        
        # Останавливаем мониторинг системы
        self.system_monitor.stop_monitoring()
        
        # Сбрасываем флаг работы
        self.is_running = False
        
        # Ожидаем завершения планировщика
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("Менеджер мониторинга остановлен")
    
    def _scheduler_loop(self) -> None:
        """Цикл планировщика задач."""
        while self.is_running:
            try:
                # Проверка и синхронизация серверов в базе данных
                self._sync_servers()
                
                # Очистка старых метрик
                self._cleanup_old_metrics()
                
                # Сон перед следующей итерацией
                time.sleep(60)  # Раз в минуту
                
            except Exception as e:
                self.logger.error(f"Ошибка в планировщике задач: {e}")
                time.sleep(60)
    
    def _handle_system_metrics(self, metrics: Dict) -> None:
        """
        Обработка новых метрик системы.
        
        Args:
            metrics: Словарь с метриками
        """
        try:
            # Отправляем обновление через WebSocket
            socketio.emit('metrics_update', metrics)
            
            # Проверяем метрики на соответствие правилам оповещений
            self.alert_manager.check_system_metrics(metrics)
            
            # Сохраняем метрики в базу данных (каждые 5 минут)
            current_minute = datetime.now().minute
            if current_minute % 5 == 0:
                self._save_system_metrics(metrics)
            
        except Exception as e:
            self.logger.error(f"Ошибка при обработке метрик системы: {e}")
    
    def _save_system_metrics(self, metrics: Dict) -> None:
        """
        Сохранение метрик системы в базу данных.
        
        Args:
            metrics: Словарь с метриками
        """
        try:
            # Получаем или создаем запись локального сервера
            local_server = Server.query.filter_by(hostname='localhost').first()
            
            if not local_server:
                local_server = Server(
                    name='Локальная система',
                    hostname='localhost',
                    ip_address='127.0.0.1',
                    status='online',
                    os_type=metrics['system_info']['platform'],
                    location='Локальный сервер',
                    description='Мониторинг локальной системы'
                )
                db.session.add(local_server)
                db.session.commit()
            
            # Обновляем статус сервера
            local_server.status = 'online'
            local_server.last_check = datetime.now()
            
            # Создаем метрики для каждого типа
            for metric_type in ['cpu', 'memory', 'disk', 'network']:
                if metric_type in metrics:
                    server_metric = ServerMetric(
                        server_id=local_server.id,
                        metric_type=metric_type,
                        timestamp=datetime.now()
                    )
                    server_metric.metric_data = metrics[metric_type]
                    db.session.add(server_metric)
            
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Ошибка при сохранении метрик в базу данных: {e}")
    
    def _sync_servers(self) -> None:
        """Синхронизация списка серверов."""
        try:
            # Здесь можно реализовать обнаружение серверов в сети
            # или синхронизацию с внешним источником данных
            pass
            
        except Exception as e:
            self.logger.error(f"Ошибка при синхронизации серверов: {e}")
    
    def _cleanup_old_metrics(self) -> None:
        """Очистка старых метрик."""
        try:
            # Удаляем метрики старше 30 дней
            thirty_days_ago = datetime.now() - timedelta(days=30)
            
            ServerMetric.query.filter(ServerMetric.timestamp < thirty_days_ago).delete()
            db.session.commit()
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Ошибка при очистке старых метрик: {e}")
