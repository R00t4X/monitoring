"""
Мониторинг локальной системы.
"""
import platform
import socket
import random
from datetime import datetime

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

class SystemMonitor:
    def __init__(self):
        self.available = PSUTIL_AVAILABLE
    
    def get_all_metrics(self):
        """Получение всех метрик"""
        if not self.available:
            return self._get_mock_metrics()
        
        return {
            'system': self._get_system_info(),
            'cpu': self._get_cpu_metrics(),
            'memory': self._get_memory_metrics(),
            'disk': self._get_disk_metrics(),
            'network': self._get_network_metrics(),
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_mock_metrics(self):
        """Имитация метрик"""
        return {
            'system': {
                'hostname': socket.gethostname(),
                'platform': platform.system(),
                'architecture': platform.machine()
            },
            'cpu': {'percent': random.randint(10, 80), 'mock': True},
            'memory': {'percent': random.randint(30, 90), 'mock': True},
            'disk': [{'device': 'Mock', 'percent': random.randint(20, 70)}],
            'network': {'bytes_sent': random.randint(1000, 9999), 'mock': True},
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_system_info(self):
        return {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'architecture': platform.machine(),
            'cpu_count': psutil.cpu_count()
        }
    
    def _get_cpu_metrics(self):
        return {
            'percent': round(psutil.cpu_percent(interval=1), 1),
            'count': psutil.cpu_count()
        }
    
    def _get_memory_metrics(self):
        mem = psutil.virtual_memory()
        return {
            'total': round(mem.total / 1024**3, 2),
            'used': round(mem.used / 1024**3, 2),
            'percent': round(mem.percent, 1)
        }
    
    def _get_disk_metrics(self):
        disks = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disks.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'total': round(usage.total / 1024**3, 2),
                    'used': round(usage.used / 1024**3, 2),
                    'percent': round((usage.used / usage.total) * 100, 1)
                })
            except PermissionError:
                continue
        return disks
    
    def _get_network_metrics(self):
        net = psutil.net_io_counters()
        return {
            'bytes_sent': round(net.bytes_sent / 1024**2, 2),
            'bytes_recv': round(net.bytes_recv / 1024**2, 2),
            'packets_sent': net.packets_sent,
            'packets_recv': net.packets_recv
        }
