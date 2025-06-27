"""
Планировщик автоматического мониторинга серверов.
"""
import threading
import time
import logging
from datetime import datetime

class MonitorScheduler:
    def __init__(self, db_manager, ssh_monitor):
        self.db_manager = db_manager
        self.ssh_monitor = ssh_monitor
        self.logger = logging.getLogger('scheduler')
        self.running = False
        self.thread = None
        self.interval = 60  # Интервал по умолчанию 60 секунд (1 минута)
        
    def start(self, interval=None):  # None означает использовать текущий интервал
        """Запуск планировщика"""
        try:
            if self.running:
                self.logger.warning("Планировщик уже запущен")
                return
                
            # Обновляем интервал только если передан новый
            if interval is not None:
                self.interval = interval
                
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            self.logger.info(f"Планировщик запущен с интервалом {self.interval} секунд")
        except Exception as e:
            self.logger.error(f"Ошибка запуска планировщика: {e}")
            self.running = False
            raise
    
    def stop(self):
        """Остановка планировщика"""
        try:
            if not self.running:
                self.logger.warning("Планировщик уже остановлен")
                return
                
            self.running = False
            if self.thread and self.thread.is_alive():
                self.thread.join(timeout=5)  # Ждем максимум 5 секунд
            self.logger.info("Планировщик остановлен")
        except Exception as e:
            self.logger.error(f"Ошибка остановки планировщика: {e}")
            raise
    
    def _monitor_loop(self):
        """Основной цикл мониторинга"""
        while self.running:
            try:
                self._check_all_servers()
                time.sleep(self.interval)
            except Exception as e:
                self.logger.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(60)  # Пауза при ошибке
    
    def _check_all_servers(self):
        """Проверка всех серверов"""
        try:
            servers = self.db_manager.get_all_servers()
            self.logger.info(f"Проверка {len(servers)} серверов")
            
            for server in servers:
                self._check_server(server)
                
        except Exception as e:
            self.logger.error(f"Ошибка получения списка серверов: {e}")
    
    def _check_server(self, server):
        """Проверка одного сервера"""
        try:
            # Тестируем подключение
            test_result = self.ssh_monitor.test_connection(
                host=server['ip'],
                port=server['port'],
                username=server['username']
            )
            
            if test_result['success']:
                # Получаем метрики
                metrics = self.ssh_monitor.get_metrics(
                    host=server['ip'],
                    port=server['port'], 
                    username=server['username']
                )
                
                if 'error' not in metrics:
                    status = 'online'
                    # Проверяем пороги
                    if metrics.get('cpu', 0) > 90 or metrics.get('memory', 0) > 95:
                        status = 'warning'
                    
                    self.db_manager.update_server_status(server['id'], status, metrics)
                    self.logger.info(f"Сервер {server['name']}: {status}")
                else:
                    self.db_manager.update_server_status(server['id'], 'offline')
                    self.logger.warning(f"Сервер {server['name']}: offline (ошибка метрик)")
            else:
                self.db_manager.update_server_status(server['id'], 'offline')
                self.logger.warning(f"Сервер {server['name']}: offline (нет подключения)")
                
        except Exception as e:
            self.logger.error(f"Ошибка проверки сервера {server['name']}: {e}")
            self.db_manager.update_server_status(server['id'], 'offline')
    
    def set_interval(self, interval):
        """Изменение интервала мониторинга"""
        self.interval = interval
        self.logger.info(f"Интервал мониторинга изменен на {interval} секунд")
    
    def get_status(self):
        """Получение статуса планировщика"""
        return {
            'running': self.running,
            'interval': self.interval,
            'thread_alive': self.thread.is_alive() if self.thread else False
        }
