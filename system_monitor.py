import psutil
import platform
import socket
from datetime import datetime, timedelta
import json
import os

# Безопасный импорт cpuinfo
try:
    from cpuinfo import get_cpu_info
    CPUINFO_AVAILABLE = True
except ImportError:
    CPUINFO_AVAILABLE = False
    def get_cpu_info():
        return {'brand_raw': platform.processor() or 'Unknown'}

class SystemMonitor:
    def __init__(self):
        if CPUINFO_AVAILABLE:
            self.cpu_info = get_cpu_info()
        else:
            self.cpu_info = {'brand_raw': platform.processor() or 'Unknown CPU'}
        self.hostname = socket.gethostname()
        self.boot_time = datetime.fromtimestamp(psutil.boot_time())
        
    def get_system_info(self):
        """Получение общей информации о системе"""
        try:
            return {
                'hostname': self.hostname,
                'platform': platform.system(),
                'platform_release': platform.release(),
                'platform_version': platform.version(),
                'architecture': platform.machine(),
                'processor': self.cpu_info.get('brand_raw', 'Unknown'),
                'cpu_count': psutil.cpu_count(),
                'cpu_count_logical': psutil.cpu_count(logical=True),
                'boot_time': self.boot_time.strftime('%Y-%m-%d %H:%M:%S'),
                'uptime': str(datetime.now() - self.boot_time).split('.')[0]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_cpu_usage(self):
        """Получение данных использования CPU"""
        try:
            cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
            cpu_freq = psutil.cpu_freq()
            
            return {
                'total': round(psutil.cpu_percent(interval=1), 1),
                'per_core': [round(x, 1) for x in cpu_percent],
                'frequency_current': round(cpu_freq.current, 2) if cpu_freq else 0,
                'frequency_max': round(cpu_freq.max, 2) if cpu_freq else 0,
                'load_average': list(os.getloadavg()) if hasattr(os, 'getloadavg') else [0, 0, 0]
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_memory_usage(self):
        """Получение данных использования памяти"""
        try:
            memory = psutil.virtual_memory()
            swap = psutil.swap_memory()
            
            return {
                'total': self._bytes_to_gb(memory.total),
                'available': self._bytes_to_gb(memory.available),
                'used': self._bytes_to_gb(memory.used),
                'free': self._bytes_to_gb(memory.free),
                'percent': round(memory.percent, 1),
                'swap_total': self._bytes_to_gb(swap.total),
                'swap_used': self._bytes_to_gb(swap.used),
                'swap_percent': round(swap.percent, 1) if swap.total > 0 else 0
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_disk_usage(self):
        """Получение данных использования дисков"""
        try:
            disk_usage = []
            partitions = psutil.disk_partitions()
            
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_info = {
                        'device': partition.device,
                        'mountpoint': partition.mountpoint,
                        'fstype': partition.fstype,
                        'total': self._bytes_to_gb(usage.total),
                        'used': self._bytes_to_gb(usage.used),
                        'free': self._bytes_to_gb(usage.free),
                        'percent': round((usage.used / usage.total) * 100, 1) if usage.total > 0 else 0
                    }
                    disk_usage.append(disk_info)
                except PermissionError:
                    continue
            
            return disk_usage
        except Exception as e:
            return {'error': str(e)}
    
    def get_network_usage(self):
        """Получение данных сетевой активности"""
        try:
            net_io = psutil.net_io_counters()
            net_connections = len(psutil.net_connections())
            
            return {
                'bytes_sent': self._bytes_to_mb(net_io.bytes_sent),
                'bytes_recv': self._bytes_to_mb(net_io.bytes_recv),
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'errors_in': net_io.errin,
                'errors_out': net_io.errout,
                'connections': net_connections
            }
        except Exception as e:
            return {'error': str(e)}
    
    def get_processes_info(self, limit=10):
        """Получение информации о процессах"""
        try:
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'username']):
                try:
                    proc_info = proc.info
                    proc_info['cpu_percent'] = round(proc_info['cpu_percent'] or 0, 1)
                    proc_info['memory_percent'] = round(proc_info['memory_percent'] or 0, 1)
                    processes.append(proc_info)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Сортировка по использованию CPU
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            return processes[:limit]
        except Exception as e:
            return {'error': str(e)}
    
    def get_temperature(self):
        """Получение температуры системы"""
        try:
            temps = psutil.sensors_temperatures()
            temp_data = {}
            
            for name, entries in temps.items():
                temp_data[name] = []
                for entry in entries:
                    temp_data[name].append({
                        'label': entry.label or 'Unknown',
                        'current': round(entry.current, 1),
                        'high': round(entry.high, 1) if entry.high else None,
                        'critical': round(entry.critical, 1) if entry.critical else None
                    })
            
            return temp_data
        except Exception as e:
            return {'error': str(e)}
    
    def get_full_report(self):
        """Получение полного отчета о системе"""
        return {
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'system_info': self.get_system_info(),
            'cpu': self.get_cpu_usage(),
            'memory': self.get_memory_usage(),
            'disk': self.get_disk_usage(),
            'network': self.get_network_usage(),
            'processes': self.get_processes_info(15),
            'temperature': self.get_temperature()
        }
    
    def _bytes_to_gb(self, bytes_value):
        """Конвертация байт в гигабайты"""
        return round(bytes_value / (1024**3), 2)
    
    def _bytes_to_mb(self, bytes_value):
        """Конвертация байт в мегабайты"""
        return round(bytes_value / (1024**2), 2)

# Глобальный экземпляр монитора
system_monitor = SystemMonitor()
