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
        
    def start(self, interval=300):  # 5 минут по умолчанию
        """Запуск планировщика"""
        if self.running:
            return
            
        self.running = True
        self.interval = interval
        self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.thread.start()
        self.logger.info(f"Планировщик запущен с интервалом {interval} секунд")
    
    def stop(self):
        """Остановка планировщика"""
        self.running = False
        if self.thread:
            self.thread.join()
        self.logger.info("Планировщик остановлен")
    
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
