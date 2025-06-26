"""
Мониторинг локальной системы.
"""
import os
import platform
import socket
import logging
import random
from datetime import datetime
from collections import deque
from typing import Dict, Optional

# Безопасный импорт psutil
try:
    import psutil
    PSUTIL_AVAILABLE = True
    PSUTIL_FUNCTIONAL = True
except ImportError:
    PSUTIL_AVAILABLE = False
    PSUTIL_FUNCTIONAL = False
    logging.warning("psutil недоступен - будут использованы заглушки")

# Безопасный импорт cpuinfo
try:
    from cpuinfo import get_cpu_info
    CPUINFO_AVAILABLE = True
    CPUINFO_FUNCTIONAL = True
except ImportError:
    CPUINFO_AVAILABLE = False
    CPUINFO_FUNCTIONAL = False
    def get_cpu_info():
        return {'brand_raw': platform.processor() or 'Unknown CPU'}

class SystemMonitor:
    """Мониторинг параметров локальной системы."""
    
    def __init__(self, history_size: int = 100):
        self.history_size = history_size
        self.metrics_history = {
            'cpu': deque(maxlen=history_size),
            'memory': deque(maxlen=history_size),
            'disk': deque(maxlen=history_size),
            'network': deque(maxlen=history_size),
        }
        
        self.logger = logging.getLogger('system_monitor')
        self.callbacks = []
        
        # Добавляем информацию о доступности модулей
        self.modules_status = {
            'psutil_available': PSUTIL_AVAILABLE,
            'psutil_functional': PSUTIL_FUNCTIONAL,
            'cpuinfo_available': CPUINFO_AVAILABLE,
            'cpuinfo_functional': CPUINFO_FUNCTIONAL
        }
    
    def get_system_info(self) -> Dict:
        """Получение основной информации о системе."""
        info = {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'platform_release': platform.release(),
            'architecture': platform.machine(),
            'uptime': 'Неизвестно',
            'modules_status': self.modules_status
        }
        
        if PSUTIL_FUNCTIONAL:
            try:
                boot_time = datetime.fromtimestamp(psutil.boot_time())
                uptime = datetime.now() - boot_time
                info['uptime'] = str(uptime).split('.')[0]
                info['cpu_count'] = psutil.cpu_count()
            except Exception as e:
                self.logger.error(f"Ошибка получения системной информации: {e}")
        
        if CPUINFO_FUNCTIONAL:
            try:
                cpu_info = get_cpu_info()
                info['processor'] = cpu_info.get('brand_raw', 'Unknown')
            except Exception:
                info['processor'] = platform.processor() or 'Unknown'
        else:
            info['processor'] = platform.processor() or 'Unknown'
        
        return info
    
    def get_cpu_usage(self) -> Dict:
        """Получение данных использования CPU."""
        if not PSUTIL_FUNCTIONAL:
            return {
                'total': random.randint(10, 30),
                'simulated': True,
                'note': 'Показаны имитированные данные (psutil недоступен)',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_freq = psutil.cpu_freq()
            
            metrics = {
                'total': round(cpu_percent, 1),
                'frequency_current': round(cpu_freq.current, 2) if cpu_freq else 0,
                'timestamp': datetime.now().isoformat()
            }
            
            self.metrics_history['cpu'].append(metrics)
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка получения CPU метрик: {e}")
            return {
                'total': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_memory_usage(self) -> Dict:
        """Получение данных использования памяти."""
        if not PSUTIL_FUNCTIONAL:
            return {
                'percent': random.randint(40, 70),
                'total': 8.0,
                'used': random.randint(3, 6),
                'simulated': True,
                'note': 'Показаны имитированные данные (psutil недоступен)',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            memory = psutil.virtual_memory()
            
            metrics = {
                'total': round(memory.total / (1024**3), 2),
                'used': round(memory.used / (1024**3), 2),
                'percent': round(memory.percent, 1),
                'timestamp': datetime.now().isoformat()
            }
            
            self.metrics_history['memory'].append(metrics)
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка получения памяти метрик: {e}")
            return {
                'percent': 0,
                'total': 0,
                'used': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_disk_usage(self) -> list:
        """Получение данных использования дисков."""
        if not PSUTIL_FUNCTIONAL:
            return [{
                'device': '/dev/sda1 (имитация)',
                'mountpoint': '/',
                'total': 100.0,
                'used': random.randint(30, 70),
                'percent': random.randint(30, 70),
                'simulated': True,
                'note': 'Показаны имитированные данные'
            }]
        
        try:
            disk_usage = []
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'total': round(usage.total / (1024**3), 2),
                        'used': round(usage.used / (1024**3), 2),
                        'percent': round((usage.used / usage.total) * 100, 1) if usage.total > 0 else 0
                    }
                    disk_usage.append(disk_info)
                except (PermissionError, OSError):
                    continue
            
            return disk_usage if disk_usage else [{'device': 'No accessible disks', 'percent': 0}]
            
        except Exception as e:
            self.logger.error(f"Ошибка получения дисковых метрик: {e}")
            return [{'device': 'Error', 'percent': 0, 'error': str(e)}]
    
    def get_network_usage(self) -> Dict:
        """Получение сетевых данных."""
        if not PSUTIL_FUNCTIONAL:
            return {
                'bytes_sent': random.randint(100, 1000),
                'bytes_recv': random.randint(500, 2000),
                'packets_sent': random.randint(10000, 50000),
                'packets_recv': random.randint(20000, 80000),
                'simulated': True,
                'note': 'Показаны имитированные данные (psutil недоступен)',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            net_io = psutil.net_io_counters()
            
            metrics = {
                'bytes_sent': round(net_io.bytes_sent / (1024**2), 2),
                'bytes_recv': round(net_io.bytes_recv / (1024**2), 2),
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'timestamp': datetime.now().isoformat()
            }
            
            self.metrics_history['network'].append(metrics)
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка получения сетевых метрик: {e}")
            return {
                'bytes_sent': 0,
                'bytes_recv': 0,
                'packets_sent': 0,
                'packets_recv': 0,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_all_metrics(self) -> Dict:
        """Получение всех метрик."""
        try:
            metrics = {
                'system_info': self.get_system_info(),
                'cpu': self.get_cpu_usage(),
                'memory': self.get_memory_usage(),
                'disk': self.get_disk_usage(),
                'network': self.get_network_usage(),
                'timestamp': datetime.now().isoformat(),
                'psutil_available': PSUTIL_AVAILABLE,
                'cpuinfo_available': CPUINFO_AVAILABLE
            }
            
            # Проверяем, что все основные метрики получены
            required_keys = ['system_info', 'cpu', 'memory', 'disk', 'network']
            for key in required_keys:
                if key not in metrics or metrics[key] is None:
                    self.logger.error(f"Отсутствует метрика: {key}")
                    metrics[key] = {'error': f'Метрика {key} недоступна'}
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Критическая ошибка получения метрик: {e}")
            # Возвращаем базовые данные в случае ошибки
            return {
                'system_info': {
                    'hostname': socket.gethostname(),
                    'platform': platform.system(),
                    'architecture': platform.machine(),
                    'uptime': 'Неизвестно',
                    'error': 'Базовые данные'
                },
                'cpu': {'total': 0, 'error': 'Недоступно'},
                'memory': {'percent': 0, 'total': 0, 'used': 0, 'error': 'Недоступно'},
                'disk': [{'device': 'Недоступно', 'percent': 0, 'total': 0, 'used': 0, 'error': 'Недоступно'}],
                'network': {'bytes_sent': 0, 'bytes_recv': 0, 'packets_sent': 0, 'packets_recv': 0, 'error': 'Недоступно'},
                'timestamp': datetime.now().isoformat(),
                'psutil_available': PSUTIL_AVAILABLE,
                'cpuinfo_available': CPUINFO_AVAILABLE,
                'critical_error': str(e)
            }
    
    def add_callback(self, callback):
        """Добавление колбэка."""
        self.callbacks.append(callback)

# Создаем глобальный экземпляр
system_monitor = SystemMonitor()
