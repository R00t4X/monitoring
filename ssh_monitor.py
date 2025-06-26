"""
SSH мониторинг удаленных серверов.
"""
import paramiko
import socket
import time
import json
import logging
from datetime import datetime
from typing import Dict, Optional, List
import threading

# Безопасный импорт paramiko
try:
    import paramiko
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False
    logging.warning("paramiko недоступен - SSH мониторинг отключен")

class SSHMonitor:
    def __init__(self):
        self.logger = logging.getLogger('ssh_monitor')
        self.active_connections = {}
        self.monitoring_active = False
        self.monitoring_thread = None
    
    def test_ssh_connection(self, host: str, port: int = 22, username: str = 'root', 
                           key_path: str = None, password: str = None, timeout: int = 10) -> Dict:
        """Тестирование SSH подключения"""
        if not SSH_AVAILABLE:
            return {
                'success': False,
                'error': 'SSH мониторинг недоступен (paramiko не установлен)',
                'suggestion': 'Установите: pip install paramiko'
            }
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Попытка подключения
            if key_path and os.path.exists(key_path):
                ssh.connect(host, port=port, username=username, 
                           key_filename=key_path, timeout=timeout)
            elif password:
                ssh.connect(host, port=port, username=username, 
                           password=password, timeout=timeout)
            else:
                # Попытка подключения без пароля (ключи SSH agent)
                ssh.connect(host, port=port, username=username, timeout=timeout)
            
            # Простая команда для проверки
            stdin, stdout, stderr = ssh.exec_command('echo "SSH OK"')
            result = stdout.read().decode().strip()
            
            ssh.close()
            
            if result == "SSH OK":
                return {
                    'success': True,
                    'message': 'SSH подключение успешно',
                    'host': host,
                    'port': port,
                    'username': username
                }
            else:
                return {
                    'success': False,
                    'error': 'Неожиданный ответ сервера'
                }
                
        except paramiko.AuthenticationException:
            return {
                'success': False,
                'error': 'Ошибка аутентификации',
                'suggestion': 'Проверьте имя пользователя и пароль/ключ'
            }
        except paramiko.SSHException as e:
            return {
                'success': False,
                'error': f'SSH ошибка: {str(e)}',
                'suggestion': 'Проверьте настройки SSH сервера'
            }
        except socket.timeout:
            return {
                'success': False,
                'error': 'Таймаут подключения',
                'suggestion': 'Проверьте доступность хоста и порта'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Неизвестная ошибка: {str(e)}'
            }
    
    def get_server_metrics(self, host: str, port: int = 22, username: str = 'root',
                          key_path: str = None, password: str = None) -> Dict:
        """Получение метрик сервера через SSH"""
        if not SSH_AVAILABLE:
            return {
                'error': 'SSH мониторинг недоступен',
                'simulated': True,
                'cpu': 25.5,
                'memory': 67.2,
                'disk': 45.8,
                'network_in': 1250,
                'network_out': 890,
                'uptime': '15 дней 8 часов',
                'timestamp': datetime.now().isoformat()
            }
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            
            # Подключение
            if key_path and os.path.exists(key_path):
                ssh.connect(host, port=port, username=username, 
                           key_filename=key_path, timeout=10)
            elif password:
                ssh.connect(host, port=port, username=username, 
                           password=password, timeout=10)
            else:
                ssh.connect(host, port=port, username=username, timeout=10)
            
            metrics = {}
            
            # CPU usage
            try:
                stdin, stdout, stderr = ssh.exec_command(
                    "top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1"
                )
                cpu_usage = stdout.read().decode().strip()
                metrics['cpu'] = float(cpu_usage) if cpu_usage else 0
            except:
                metrics['cpu'] = 0
            
            # Memory usage
            try:
                stdin, stdout, stderr = ssh.exec_command(
                    "free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'"
                )
                memory_usage = stdout.read().decode().strip()
                metrics['memory'] = float(memory_usage) if memory_usage else 0
            except:
                metrics['memory'] = 0
            
            # Disk usage (root partition)
            try:
                stdin, stdout, stderr = ssh.exec_command(
                    "df -h / | awk 'NR==2{print $5}' | cut -d'%' -f1"
                )
                disk_usage = stdout.read().decode().strip()
                metrics['disk'] = float(disk_usage) if disk_usage else 0
            except:
                metrics['disk'] = 0
            
            # Network statistics
            try:
                stdin, stdout, stderr = ssh.exec_command(
                    "cat /proc/net/dev | grep -E '(eth0|ens|enp)' | head -1 | awk '{print $2\" \"$10}'"
                )
                net_stats = stdout.read().decode().strip().split()
                if len(net_stats) >= 2:
                    metrics['network_in'] = int(net_stats[0]) // (1024*1024)  # MB
                    metrics['network_out'] = int(net_stats[1]) // (1024*1024)  # MB
                else:
                    metrics['network_in'] = 0
                    metrics['network_out'] = 0
            except:
                metrics['network_in'] = 0
                metrics['network_out'] = 0
            
            # Uptime
            try:
                stdin, stdout, stderr = ssh.exec_command("uptime -p")
                uptime = stdout.read().decode().strip()
                metrics['uptime'] = uptime.replace('up ', '') if uptime else 'unknown'
            except:
                metrics['uptime'] = 'unknown'
            
            # System info
            try:
                stdin, stdout, stderr = ssh.exec_command("uname -a")
                system_info = stdout.read().decode().strip()
                metrics['system_info'] = system_info
            except:
                metrics['system_info'] = 'unknown'
            
            # Load average
            try:
                stdin, stdout, stderr = ssh.exec_command("uptime | awk -F'load average:' '{print $2}'")
                load_avg = stdout.read().decode().strip()
                metrics['load_average'] = load_avg
            except:
                metrics['load_average'] = 'unknown'
            
            ssh.close()
            
            # Определяем статус на основе метрик
            status = 'online'
            if metrics['cpu'] > 90 or metrics['memory'] > 95:
                status = 'warning'
            
            metrics.update({
                'status': status,
                'timestamp': datetime.now().isoformat(),
                'ssh_success': True
            })
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Ошибка получения метрик SSH для {host}: {e}")
            return {
                'error': str(e),
                'status': 'offline',
                'cpu': 0,
                'memory': 0,
                'disk': 0,
                'network_in': 0,
                'network_out': 0,
                'uptime': 'unknown',
                'timestamp': datetime.now().isoformat(),
                'ssh_success': False
            }
    
    def monitor_server_continuously(self, server_config: Dict, interval: int = 60):
        """Непрерывный мониторинг сервера"""
        server_id = server_config.get('id')
        
        while self.monitoring_active and server_id in self.active_connections:
            try:
                metrics = self.get_server_metrics(
                    host=server_config.get('ip'),
                    port=server_config.get('port', 22),
                    username=server_config.get('username', 'root'),
                    key_path=server_config.get('key_path'),
                    password=server_config.get('password')
                )
                
                # Обновляем метрики в базе данных
                if hasattr(self, 'update_callback') and self.update_callback:
                    self.update_callback(server_id, metrics)
                
                time.sleep(interval)
                
            except Exception as e:
                self.logger.error(f"Ошибка в мониторинге сервера {server_id}: {e}")
                time.sleep(interval)
    
    def start_monitoring_server(self, server_config: Dict, interval: int = 60):
        """Запуск мониторинга сервера"""
        server_id = server_config.get('id')
        
        if server_id in self.active_connections:
            self.logger.warning(f"Мониторинг сервера {server_id} уже запущен")
            return
        
        # Создаем поток мониторинга
        monitor_thread = threading.Thread(
            target=self.monitor_server_continuously,
            args=(server_config, interval),
            daemon=True
        )
        
        self.active_connections[server_id] = {
            'thread': monitor_thread,
            'config': server_config,
            'started_at': datetime.now()
        }
        
        self.monitoring_active = True
        monitor_thread.start()
        
        self.logger.info(f"Запущен мониторинг сервера {server_config.get('name')} ({server_config.get('ip')})")
    
    def stop_monitoring_server(self, server_id: int):
        """Остановка мониторинга сервера"""
        if server_id in self.active_connections:
            del self.active_connections[server_id]
            self.logger.info(f"Остановлен мониторинг сервера {server_id}")
    
    def stop_all_monitoring(self):
        """Остановка всего мониторинга"""
        self.monitoring_active = False
        self.active_connections.clear()
        self.logger.info("Остановлен весь SSH мониторинг")
    
    def get_monitoring_status(self) -> Dict:
        """Получение статуса мониторинга"""
        return {
            'active': self.monitoring_active,
            'monitored_servers': len(self.active_connections),
            'ssh_available': SSH_AVAILABLE,
            'connections': {
                server_id: {
                    'server_name': conn['config'].get('name'),
                    'server_ip': conn['config'].get('ip'),
                    'started_at': conn['started_at'].isoformat()
                }
                for server_id, conn in self.active_connections.items()
            }
        }

# Глобальный экземпляр SSH монитора
ssh_monitor = SSHMonitor()
