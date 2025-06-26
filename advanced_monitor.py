import psutil
import time
import json
import socket
import subprocess
import threading
from datetime import datetime, timedelta
from collections import deque
import numpy as np
from typing import Dict, List, Optional
import logging

try:
    from cpuinfo import get_cpu_info
    CPUINFO_AVAILABLE = True
except ImportError:
    CPUINFO_AVAILABLE = False

class AdvancedSystemMonitor:
    def __init__(self, history_size=1000):
        self.history_size = history_size
        self.metrics_history = {
            'cpu': deque(maxlen=history_size),
            'memory': deque(maxlen=history_size),
            'disk': deque(maxlen=history_size),
            'network': deque(maxlen=history_size),
            'processes': deque(maxlen=history_size),
            'temperatures': deque(maxlen=history_size)
        }
        
        self.last_network_stats = None
        self.last_disk_stats = None
        self.monitoring_active = False
        self.monitoring_thread = None
        self.callbacks = []
        
        # Получаем базовую информацию о системе
        self.system_info = self._get_system_info()
        
    def _get_system_info(self):
        """Получение детальной информации о системе"""
        info = {
            'hostname': socket.gethostname(),
            'platform': psutil.LINUX if hasattr(psutil, 'LINUX') else 'unknown',
            'boot_time': datetime.fromtimestamp(psutil.boot_time()),
            'cpu_count_physical': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count(logical=True),
        }
        
        if CPUINFO_AVAILABLE:
            cpu_info = get_cpu_info()
            info.update({
                'cpu_brand': cpu_info.get('brand_raw', 'Unknown'),
                'cpu_arch': cpu_info.get('arch', 'Unknown'),
                'cpu_bits': cpu_info.get('bits', 'Unknown'),
                'cpu_hz': cpu_info.get('hz_actual_friendly', 'Unknown')
            })
        
        return info
    
    def get_advanced_cpu_metrics(self):
        """Расширенные метрики CPU"""
        try:
            # Базовые метрики
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_per_core = psutil.cpu_percent(interval=1, percpu=True)
            
            # Частота процессора
            cpu_freq = psutil.cpu_freq()
            
            # Загрузка системы
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            # Статистика CPU
            cpu_stats = psutil.cpu_stats()
            
            # Времена CPU
            cpu_times = psutil.cpu_times()
            
            metrics = {
                'usage_total': round(cpu_percent, 2),
                'usage_per_core': [round(x, 2) for x in cpu_per_core],
                'frequency_current': round(cpu_freq.current, 2) if cpu_freq else 0,
                'frequency_min': round(cpu_freq.min, 2) if cpu_freq else 0,
                'frequency_max': round(cpu_freq.max, 2) if cpu_freq else 0,
                'load_avg_1': round(load_avg[0], 2),
                'load_avg_5': round(load_avg[1], 2),
                'load_avg_15': round(load_avg[2], 2),
                'ctx_switches': cpu_stats.ctx_switches,
                'interrupts': cpu_stats.interrupts,
                'soft_interrupts': cpu_stats.soft_interrupts,
                'syscalls': getattr(cpu_stats, 'syscalls', 0),
                'idle_time': round(cpu_times.idle, 2),
                'user_time': round(cpu_times.user, 2),
                'system_time': round(cpu_times.system, 2),
                'timestamp': datetime.now().isoformat()
            }
            
            self.metrics_history['cpu'].append(metrics)
            return metrics
            
        except Exception as e:
            logging.error(f"Error getting CPU metrics: {e}")
            return {}
    
    def get_advanced_memory_metrics(self):
        """Расширенные метрики памяти"""
        try:
            # Виртуальная память
            vmem = psutil.virtual_memory()
            
            # Swap память
            swap = psutil.swap_memory()
            
            metrics = {
                'total': vmem.total,
                'available': vmem.available,
                'used': vmem.used,
                'free': vmem.free,
                'percent': round(vmem.percent, 2),
                'active': getattr(vmem, 'active', 0),
                'inactive': getattr(vmem, 'inactive', 0),
                'buffers': getattr(vmem, 'buffers', 0),
                'cached': getattr(vmem, 'cached', 0),
                'shared': getattr(vmem, 'shared', 0),
                'slab': getattr(vmem, 'slab', 0),
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_free': swap.free,
                'swap_percent': round(swap.percent, 2) if swap.total > 0 else 0,
                'swap_in': getattr(swap, 'sin', 0),
                'swap_out': getattr(swap, 'sout', 0),
                'timestamp': datetime.now().isoformat()
            }
            
            self.metrics_history['memory'].append(metrics)
            return metrics
            
        except Exception as e:
            logging.error(f"Error getting memory metrics: {e}")
            return {}
    
    def get_advanced_disk_metrics(self):
        """Расширенные метрики дисков"""
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
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': round((usage.used / usage.total) * 100, 2) if usage.total > 0 else 0
                    }
                    disk_usage.append(disk_info)
                except PermissionError:
                    continue
            
            # I/O статистика
            disk_io = psutil.disk_io_counters()
            io_metrics = {}
            if disk_io:
                current_time = time.time()
                if self.last_disk_stats:
                    time_delta = current_time - self.last_disk_stats['timestamp']
                    read_speed = (disk_io.read_bytes - self.last_disk_stats['read_bytes']) / time_delta
                    write_speed = (disk_io.write_bytes - self.last_disk_stats['write_bytes']) / time_delta
                    
                    io_metrics = {
                        'read_speed': round(read_speed, 2),
                        'write_speed': round(write_speed, 2),
                        'read_iops': round((disk_io.read_count - self.last_disk_stats['read_count']) / time_delta, 2),
                        'write_iops': round((disk_io.write_count - self.last_disk_stats['write_count']) / time_delta, 2)
                    }
                
                self.last_disk_stats = {
                    'timestamp': current_time,
                    'read_bytes': disk_io.read_bytes,
                    'write_bytes': disk_io.write_bytes,
                    'read_count': disk_io.read_count,
                    'write_count': disk_io.write_count
                }
            
            metrics = {
                'partitions': disk_usage,
                'io': io_metrics,
                'total_read_bytes': disk_io.read_bytes if disk_io else 0,
                'total_write_bytes': disk_io.write_bytes if disk_io else 0,
                'total_read_count': disk_io.read_count if disk_io else 0,
                'total_write_count': disk_io.write_count if disk_io else 0,
                'timestamp': datetime.now().isoformat()
            }
            
            self.metrics_history['disk'].append(metrics)
            return metrics
            
        except Exception as e:
            logging.error(f"Error getting disk metrics: {e}")
            return {}
    
    def get_advanced_network_metrics(self):
        """Расширенные сетевые метрики"""
        try:
            # Общая статистика
            net_io = psutil.net_io_counters()
            
            # Статистика по интерфейсам
            net_io_per_nic = psutil.net_io_counters(pernic=True)
            
            # Сетевые соединения
            connections = psutil.net_connections()
            
            # Подсчет соединений по состояниям
            conn_states = {}
            for conn in connections:
                state = conn.status
                conn_states[state] = conn_states.get(state, 0) + 1
            
            # Расчет скорости
            speed_metrics = {}
            if net_io and self.last_network_stats:
                current_time = time.time()
                time_delta = current_time - self.last_network_stats['timestamp']
                
                speed_metrics = {
                    'bytes_sent_per_sec': round((net_io.bytes_sent - self.last_network_stats['bytes_sent']) / time_delta, 2),
                    'bytes_recv_per_sec': round((net_io.bytes_recv - self.last_network_stats['bytes_recv']) / time_delta, 2),
                    'packets_sent_per_sec': round((net_io.packets_sent - self.last_network_stats['packets_sent']) / time_delta, 2),
                    'packets_recv_per_sec': round((net_io.packets_recv - self.last_network_stats['packets_recv']) / time_delta, 2)
                }
            
            if net_io:
                self.last_network_stats = {
                    'timestamp': time.time(),
                    'bytes_sent': net_io.bytes_sent,
                    'bytes_recv': net_io.bytes_recv,
                    'packets_sent': net_io.packets_sent,
                    'packets_recv': net_io.packets_recv
                }
            
            metrics = {
                'total_bytes_sent': net_io.bytes_sent if net_io else 0,
                'total_bytes_recv': net_io.bytes_recv if net_io else 0,
                'total_packets_sent': net_io.packets_sent if net_io else 0,
                'total_packets_recv': net_io.packets_recv if net_io else 0,
                'total_errin': net_io.errin if net_io else 0,
                'total_errout': net_io.errout if net_io else 0,
                'total_dropin': net_io.dropin if net_io else 0,
                'total_dropout': net_io.dropout if net_io else 0,
                'interfaces': {name: {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv
                } for name, stats in net_io_per_nic.items()},
                'connections_count': len(connections),
                'connections_by_state': conn_states,
                'speed': speed_metrics,
                'timestamp': datetime.now().isoformat()
            }
            
            self.metrics_history['network'].append(metrics)
            return metrics
            
        except Exception as e:
            logging.error(f"Error getting network metrics: {e}")
            return {}
    
    def get_advanced_process_metrics(self):
        """Расширенные метрики процессов"""
        try:
            processes = []
            total_processes = 0
            total_threads = 0
            total_memory = 0
            
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cpu_percent', 
                                           'memory_percent', 'memory_info', 'status', 
                                           'create_time', 'num_threads']):
                try:
                    pinfo = proc.info
                    total_processes += 1
                    total_threads += pinfo.get('num_threads', 0)
                    total_memory += pinfo.get('memory_info', psutil._psutil_linux.pmem()).rss
                    
                    if pinfo['cpu_percent'] > 0.1 or pinfo['memory_percent'] > 0.1:
                        processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'username': pinfo.get('username', 'unknown'),
                            'cpu_percent': round(pinfo.get('cpu_percent', 0), 2),
                            'memory_percent': round(pinfo.get('memory_percent', 0), 2),
                            'memory_mb': round(pinfo.get('memory_info', psutil._psutil_linux.pmem()).rss / 1024 / 1024, 2),
                            'status': pinfo.get('status', 'unknown'),
                            'threads': pinfo.get('num_threads', 0),
                            'create_time': pinfo.get('create_time', 0)
                        })
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            # Сортировка по использованию CPU
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            metrics = {
                'total_count': total_processes,
                'total_threads': total_threads,
                'total_memory_mb': round(total_memory / 1024 / 1024, 2),
                'top_processes': processes[:20],  # Топ 20 процессов
                'timestamp': datetime.now().isoformat()
            }
            
            self.metrics_history['processes'].append(metrics)
            return metrics
            
        except Exception as e:
            logging.error(f"Error getting process metrics: {e}")
            return {}
    
    def get_temperature_metrics(self):
        """Метрики температуры"""
        try:
            if not hasattr(psutil, 'sensors_temperatures'):
                return {}
            
            temps = psutil.sensors_temperatures()
            if not temps:
                return {}
            
            temperature_data = {}
            for name, entries in temps.items():
                sensor_temps = []
                for entry in entries:
                    sensor_temps.append({
                        'label': entry.label or f'{name}_sensor',
                        'current': round(entry.current, 1),
                        'high': round(entry.high, 1) if entry.high else None,
                        'critical': round(entry.critical, 1) if entry.critical else None
                    })
                temperature_data[name] = sensor_temps
            
            metrics = {
                'sensors': temperature_data,
                'timestamp': datetime.now().isoformat()
            }
            
            self.metrics_history['temperatures'].append(metrics)
            return metrics
            
        except Exception as e:
            logging.error(f"Error getting temperature metrics: {e}")
            return {}
    
    def get_comprehensive_metrics(self):
        """Получение всех метрик сразу"""
        return {
            'system_info': self.system_info,
            'cpu': self.get_advanced_cpu_metrics(),
            'memory': self.get_advanced_memory_metrics(),
            'disk': self.get_advanced_disk_metrics(),
            'network': self.get_advanced_network_metrics(),
            'processes': self.get_advanced_process_metrics(),
            'temperature': self.get_temperature_metrics(),
            'timestamp': datetime.now().isoformat(),
            'uptime': str(datetime.now() - self.system_info['boot_time']).split('.')[0]
        }
    
    def get_metrics_history(self, metric_type: str, limit: int = 100):
        """Получение истории метрик"""
        if metric_type in self.metrics_history:
            return list(self.metrics_history[metric_type])[-limit:]
        return []
    
    def calculate_trends(self, metric_type: str, field: str, period_minutes: int = 60):
        """Расчет трендов метрик"""
        try:
            history = self.get_metrics_history(metric_type, limit=period_minutes * 2)
            if len(history) < 2:
                return {'trend': 'stable', 'change_percent': 0}
            
            # Извлекаем значения
            values = []
            timestamps = []
            
            for entry in history:
                if field in entry and entry[field] is not None:
                    values.append(float(entry[field]))
                    timestamps.append(datetime.fromisoformat(entry['timestamp']))
            
            if len(values) < 2:
                return {'trend': 'stable', 'change_percent': 0}
            
            # Простой расчет тренда
            recent_avg = np.mean(values[-10:])  # Последние 10 значений
            older_avg = np.mean(values[:10])    # Первые 10 значений
            
            change_percent = ((recent_avg - older_avg) / older_avg) * 100 if older_avg != 0 else 0
            
            if abs(change_percent) < 5:
                trend = 'stable'
            elif change_percent > 0:
                trend = 'increasing'
            else:
                trend = 'decreasing'
            
            return {
                'trend': trend,
                'change_percent': round(change_percent, 2),
                'recent_avg': round(recent_avg, 2),
                'older_avg': round(older_avg, 2)
            }
            
        except Exception as e:
            logging.error(f"Error calculating trends: {e}")
            return {'trend': 'unknown', 'change_percent': 0}
    
    def start_monitoring(self, interval: int = 30):
        """Запуск мониторинга в отдельном потоке"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, 
            args=(interval,),
            daemon=True
        )
        self.monitoring_thread.start()
        logging.info(f"Advanced monitoring started with {interval}s interval")
    
    def stop_monitoring(self):
        """Остановка мониторинга"""
        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        logging.info("Advanced monitoring stopped")
    
    def _monitoring_loop(self, interval: int):
        """Основной цикл мониторинга"""
        while self.monitoring_active:
            try:
                metrics = self.get_comprehensive_metrics()
                
                # Вызываем колбэки для обновления данных
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        logging.error(f"Error in monitoring callback: {e}")
                
                time.sleep(interval)
                
            except Exception as e:
                logging.error(f"Error in monitoring loop: {e}")
                time.sleep(interval)
    
    def add_callback(self, callback):
        """Добавление колбэка для обновления данных"""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback):
        """Удаление колбэка"""
        if callback in self.callbacks:
            self.callbacks.remove(callback)

# Глобальный экземпляр продвинутого монитора
advanced_monitor = AdvancedSystemMonitor()
