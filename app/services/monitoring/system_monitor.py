"""
Мониторинг локальной системы.
"""
import os
import time
import socket
import platform
import logging
import json
import threading
from datetime import datetime
from collections import deque
from typing import Dict, List, Optional, Callable
import psutil

# Проверка доступности модуля cpuinfo
try:
    from cpuinfo import get_cpu_info
    CPUINFO_AVAILABLE = True
except ImportError:
    CPUINFO_AVAILABLE = False
    logging.warning("Модуль cpuinfo недоступен. Будет использована ограниченная информация о CPU.")

class SystemMonitor:
    """Мониторинг параметров локальной системы."""
    
    def __init__(self, history_size: int = 100):
        """
        Инициализация монитора системы.
        
        Args:
            history_size: Размер истории хранения метрик.
        """
        # Основная информация о системе
        self.system_info = self._get_system_info()
        
        # История метрик
        self.history_size = history_size
        self.metrics_history = {
            'cpu': deque(maxlen=history_size),
            'memory': deque(maxlen=history_size),
            'disk': deque(maxlen=history_size),
            'network': deque(maxlen=history_size),
            'temperature': deque(maxlen=history_size),
            'processes': deque(maxlen=history_size)
        }
        
        # Для расчета скорости передачи данных
        self._last_network_io = None
        self._last_disk_io = None
        
        # Мониторинг
        self.monitoring_active = False
        self.monitoring_thread = None
        self.monitoring_interval = 5  # секунды
        
        # Колбеки для обновления данных
        self.callbacks = []
        
        # Логирование
        self.logger = logging.getLogger('monitoring.system')
    
    def _get_system_info(self) -> Dict:
        """Получение основной информации о системе."""
        info = {
            'hostname': socket.gethostname(),
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'boot_time': datetime.fromtimestamp(psutil.boot_time()).strftime('%Y-%m-%d %H:%M:%S'),
            'cpu_count_physical': psutil.cpu_count(logical=False),
            'cpu_count_logical': psutil.cpu_count(logical=True)
        }
        
        # Добавляем подробную информацию о CPU при наличии cpuinfo
        if CPUINFO_AVAILABLE:
            try:
                cpu_info = get_cpu_info()
                info.update({
                    'cpu_brand': cpu_info.get('brand_raw', 'Unknown'),
                    'cpu_vendor': cpu_info.get('vendor_id_raw', 'Unknown'),
                    'cpu_hz': cpu_info.get('hz_actual_friendly', 'Unknown'),
                    'cpu_arch': cpu_info.get('arch', 'Unknown'),
                    'cpu_bits': cpu_info.get('bits', 'Unknown'),
                })
            except Exception as e:
                self.logger.error(f"Ошибка при получении информации о CPU: {e}")
        
        return info
    
    def get_cpu_metrics(self) -> Dict:
        """Получение метрик процессора."""
        try:
            # Общая загрузка CPU
            cpu_percent = psutil.cpu_percent(interval=0.5)
            
            # Загрузка CPU по ядрам
            cpu_percent_per_core = psutil.cpu_percent(interval=0.5, percpu=True)
            
            # Частота CPU
            cpu_freq = psutil.cpu_freq()
            if cpu_freq:
                freq_current = cpu_freq.current
                freq_min = cpu_freq.min
                freq_max = cpu_freq.max
            else:
                freq_current = freq_min = freq_max = None
            
            # Статистика CPU
            cpu_stats = psutil.cpu_stats()
            
            # Загрузка системы
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else (0, 0, 0)
            
            # Формируем метрики
            metrics = {
                'cpu_percent': round(cpu_percent, 2),
                'cpu_percent_per_core': [round(x, 2) for x in cpu_percent_per_core],
                'cpu_freq_current': round(freq_current, 2) if freq_current else None,
                'cpu_freq_min': round(freq_min, 2) if freq_min else None,
                'cpu_freq_max': round(freq_max, 2) if freq_max else None,
                'ctx_switches': cpu_stats.ctx_switches,
                'interrupts': cpu_stats.interrupts,
                'soft_interrupts': cpu_stats.soft_interrupts,
                'syscalls': getattr(cpu_stats, 'syscalls', 0),
                'load_avg_1min': round(load_avg[0], 2),
                'load_avg_5min': round(load_avg[1], 2),
                'load_avg_15min': round(load_avg[2], 2),
                'timestamp': datetime.now().isoformat()
            }
            
            # Сохраняем в историю
            self.metrics_history['cpu'].append(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении метрик CPU: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_memory_metrics(self) -> Dict:
        """Получение метрик памяти."""
        try:
            # Виртуальная память
            vm = psutil.virtual_memory()
            
            # Swap
            swap = psutil.swap_memory()
            
            # Формируем метрики
            metrics = {
                'total': vm.total,
                'available': vm.available,
                'used': vm.used,
                'free': vm.free,
                'percent': round(vm.percent, 2),
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_free': swap.free,
                'swap_percent': round(swap.percent, 2),
                # Дополнительные метрики, если доступны
                'cached': getattr(vm, 'cached', None),
                'buffers': getattr(vm, 'buffers', None),
                'shared': getattr(vm, 'shared', None),
                'timestamp': datetime.now().isoformat()
            }
            
            # Сохраняем в историю
            self.metrics_history['memory'].append(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении метрик памяти: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_disk_metrics(self) -> Dict:
        """Получение метрик дисков."""
        try:
            # Получаем информацию о разделах
            partitions = []
            for part in psutil.disk_partitions(all=False):
                try:
                    usage = psutil.disk_usage(part.mountpoint)
                    partitions.append({
                        'device': part.device,
                        'mountpoint': part.mountpoint,
                        'fstype': part.fstype,
                        'total': usage.total,
                        'used': usage.used,
                        'free': usage.free,
                        'percent': round(usage.percent, 2)
                    })
                except (PermissionError, OSError):
                    # Некоторые точки монтирования могут быть недоступны
                    continue
            
            # Получаем IO статистику
            current_io = psutil.disk_io_counters()
            current_time = time.time()
            
            # Рассчитываем скорость IO
            io_stats = {}
            if current_io and self._last_disk_io:
                time_delta = current_time - self._last_disk_io['time']
                if time_delta > 0:
                    read_speed = (current_io.read_bytes - self._last_disk_io['read_bytes']) / time_delta
                    write_speed = (current_io.write_bytes - self._last_disk_io['write_bytes']) / time_delta
                    
                    io_stats = {
                        'read_speed': round(read_speed, 2),
                        'write_speed': round(write_speed, 2),
                        'read_count': current_io.read_count,
                        'write_count': current_io.write_count,
                        'read_time': current_io.read_time,
                        'write_time': current_io.write_time
                    }
            
            # Обновляем последние значения для следующего расчета
            if current_io:
                self._last_disk_io = {
                    'time': current_time,
                    'read_bytes': current_io.read_bytes,
                    'write_bytes': current_io.write_bytes
                }
            
            # Формируем метрики
            metrics = {
                'partitions': partitions,
                'io': io_stats,
                'timestamp': datetime.now().isoformat()
            }
            
            # Сохраняем в историю
            self.metrics_history['disk'].append(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении метрик дисков: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_network_metrics(self) -> Dict:
        """Получение сетевых метрик."""
        try:
            # Получаем текущую статистику сети
            current_net_io = psutil.net_io_counters()
            current_time = time.time()
            
            # Статистика по интерфейсам
            net_interfaces = {}
            for interface, stats in psutil.net_io_counters(pernic=True).items():
                net_interfaces[interface] = {
                    'bytes_sent': stats.bytes_sent,
                    'bytes_recv': stats.bytes_recv,
                    'packets_sent': stats.packets_sent,
                    'packets_recv': stats.packets_recv,
                    'errin': stats.errin,
                    'errout': stats.errout,
                    'dropin': stats.dropin,
                    'dropout': stats.dropout
                }
            
            # Статистика соединений
            connections = {
                'total': 0,
                'by_status': {},
                'by_type': {}
            }
            
            for conn in psutil.net_connections(kind='inet'):
                connections['total'] += 1
                
                # Группировка по статусу
                status = conn.status
                connections['by_status'][status] = connections['by_status'].get(status, 0) + 1
                
                # Группировка по типу (TCP/UDP)
                conn_type = 'tcp' if conn.type == socket.SOCK_STREAM else 'udp'
                connections['by_type'][conn_type] = connections['by_type'].get(conn_type, 0) + 1
            
            # Рассчитываем скорость передачи данных
            net_speed = {
                'bytes_sent_per_sec': 0,
                'bytes_recv_per_sec': 0
            }
            
            if current_net_io and self._last_network_io:
                time_delta = current_time - self._last_network_io['time']
                if time_delta > 0:
                    bytes_sent_per_sec = (current_net_io.bytes_sent - self._last_network_io['bytes_sent']) / time_delta
                    bytes_recv_per_sec = (current_net_io.bytes_recv - self._last_network_io['bytes_recv']) / time_delta
                    
                    net_speed = {
                        'bytes_sent_per_sec': round(bytes_sent_per_sec, 2),
                        'bytes_recv_per_sec': round(bytes_recv_per_sec, 2),
                        'mbits_sent_per_sec': round(bytes_sent_per_sec * 8 / 1_000_000, 2),
                        'mbits_recv_per_sec': round(bytes_recv_per_sec * 8 / 1_000_000, 2)
                    }
            
            # Обновляем последние значения для следующего расчета
            if current_net_io:
                self._last_network_io = {
                    'time': current_time,
                    'bytes_sent': current_net_io.bytes_sent,
                    'bytes_recv': current_net_io.bytes_recv
                }
            
            # Формируем метрики
            metrics = {
                'bytes_sent': current_net_io.bytes_sent if current_net_io else 0,
                'bytes_recv': current_net_io.bytes_recv if current_net_io else 0,
                'packets_sent': current_net_io.packets_sent if current_net_io else 0,
                'packets_recv': current_net_io.packets_recv if current_net_io else 0,
                'speed': net_speed,
                'interfaces': net_interfaces,
                'connections': connections,
                'timestamp': datetime.now().isoformat()
            }
            
            # Сохраняем в историю
            self.metrics_history['network'].append(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении сетевых метрик: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_temperature_metrics(self) -> Dict:
        """Получение метрик температуры."""
        try:
            # Проверяем наличие функциональности
            if not hasattr(psutil, 'sensors_temperatures'):
                return {
                    'supported': False,
                    'message': 'Функция мониторинга температуры не поддерживается',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Получаем температуры
            temps = psutil.sensors_temperatures()
            
            # Если датчики не найдены
            if not temps:
                return {
                    'supported': True,
                    'sensors_found': False,
                    'message': 'Датчики температуры не обнаружены',
                    'timestamp': datetime.now().isoformat()
                }
            
            # Формируем структуру датчиков
            sensors = {}
            for chip, entries in temps.items():
                sensors[chip] = []
                for entry in entries:
                    sensors[chip].append({
                        'label': entry.label or f'Sensor',
                        'current': round(entry.current, 2) if entry.current else None,
                        'high': round(entry.high, 2) if entry.high else None,
                        'critical': round(entry.critical, 2) if entry.critical else None
                    })
            
            # Формируем метрики
            metrics = {
                'supported': True,
                'sensors_found': True,
                'sensors': sensors,
                'timestamp': datetime.now().isoformat()
            }
            
            # Сохраняем в историю
            self.metrics_history['temperature'].append(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении метрик температуры: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_process_metrics(self) -> Dict:
        """Получение метрик процессов."""
        try:
            # Счетчики
            total_processes = 0
            total_threads = 0
            running_processes = 0
            sleeping_processes = 0
            
            # Список процессов с наибольшей нагрузкой
            top_processes = []
            
            # Собираем информацию о процессах
            for proc in psutil.process_iter(['pid', 'name', 'username', 'cmdline', 
                                           'cpu_percent', 'memory_percent',
                                           'status', 'num_threads', 'create_time']):
                try:
                    # Обновляем счетчики
                    total_processes += 1
                    total_threads += proc.info['num_threads']
                    
                    # Статус процесса
                    status = proc.info['status']
                    if status == psutil.STATUS_RUNNING:
                        running_processes += 1
                    elif status == psutil.STATUS_SLEEPING:
                        sleeping_processes += 1
                    
                    # Добавляем в список top процессов только с ненулевой нагрузкой
                    if proc.info['cpu_percent'] > 0.1 or proc.info['memory_percent'] > 0.1:
                        proc_info = {
                            'pid': proc.info['pid'],
                            'name': proc.info['name'],
                            'username': proc.info['username'],
                            'cpu_percent': round(proc.info['cpu_percent'], 2),
                            'memory_percent': round(proc.info['memory_percent'], 2),
                            'status': proc.info['status'],
                            'threads': proc.info['num_threads'],
                            'create_time': proc.info['create_time']
                        }
                        top_processes.append(proc_info)
                
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Сортируем по CPU
            top_processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
            
            # Формируем метрики
            metrics = {
                'total_processes': total_processes,
                'total_threads': total_threads,
                'running_processes': running_processes,
                'sleeping_processes': sleeping_processes,
                'top_processes': top_processes[:20],  # Топ 20 процессов
                'timestamp': datetime.now().isoformat()
            }
            
            # Сохраняем в историю
            self.metrics_history['processes'].append(metrics)
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка при получении метрик процессов: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def get_all_metrics(self) -> Dict:
        """Получение всех метрик одновременно."""
        return {
            'system_info': self.system_info,
            'cpu': self.get_cpu_metrics(),
            'memory': self.get_memory_metrics(),
            'disk': self.get_disk_metrics(),
            'network': self.get_network_metrics(),
            'temperature': self.get_temperature_metrics(),
            'processes': self.get_process_metrics(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_metrics_history(self, metric_type: str, limit: int = 100) -> List[Dict]:
        """
        Получение истории метрик определенного типа.
        
        Args:
            metric_type: Тип метрики (cpu, memory, disk, network, temperature, processes)
            limit: Максимальное количество записей
            
        Returns:
            Список словарей с метриками
        """
        if metric_type not in self.metrics_history:
            return []
        
        history = list(self.metrics_history[metric_type])
        return history[-limit:] if limit < len(history) else history
    
    def start_monitoring(self, interval: int = 5) -> None:
        """
        Запуск мониторинга в отдельном потоке.
        
        Args:
            interval: Интервал сбора метрик в секундах
        """
        if self.monitoring_active:
            self.logger.warning("Мониторинг уже запущен")
            return
        
        self.monitoring_interval = interval
        self.monitoring_active = True
        
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop,
            daemon=True
        )
        self.monitoring_thread.start()
        
        self.logger.info(f"Мониторинг запущен с интервалом {interval} сек.")
    
    def stop_monitoring(self) -> None:
        """Остановка мониторинга."""
        if not self.monitoring_active:
            return
        
        self.monitoring_active = False
        
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=3)
            
        self.logger.info("Мониторинг остановлен")
    
    def _monitoring_loop(self) -> None:
        """Основной цикл мониторинга."""
        while self.monitoring_active:
            try:
                # Получаем все метрики
                metrics = self.get_all_metrics()
                
                # Вызываем колбеки
                for callback in self.callbacks:
                    try:
                        callback(metrics)
                    except Exception as e:
                        self.logger.error(f"Ошибка в колбеке мониторинга: {e}")
                
                # Пауза между замерами
                time.sleep(self.monitoring_interval)
                
            except Exception as e:
                self.logger.error(f"Ошибка в цикле мониторинга: {e}")
                time.sleep(self.monitoring_interval)
    
    def add_callback(self, callback: Callable[[Dict], None]) -> None:
        """
        Добавление колбека для обработки новых метрик.
        
        Args:
            callback: Функция для вызова при получении новых метрик
        """
        if callback not in self.callbacks:
            self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[Dict], None]) -> None:
        """
        Удаление колбека.
        
        Args:
            callback: Функция для удаления
        """
        if callback in self.callbacks:
            self.callbacks.remove(callback)
