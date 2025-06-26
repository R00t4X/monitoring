"""
SSH мониторинг удаленных серверов.
"""
import socket

try:
    import paramiko
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False

class SSHMonitor:
    def __init__(self):
        self.available = SSH_AVAILABLE
    
    def test_connection(self, host, port=22, username='root', password=None):
        """Тестирование SSH подключения"""
        if not self.available:
            return {'success': False, 'error': 'SSH недоступен'}
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
            
            stdin, stdout, stderr = ssh.exec_command('echo "test"')
            result = stdout.read().decode().strip()
            ssh.close()
            
            return {'success': True, 'message': 'Подключение успешно'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_metrics(self, host, port=22, username='root', password=None):
        """Получение метрик через SSH"""
        if not self.available:
            return {'error': 'SSH недоступен'}
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=username, password=password, timeout=10)
            
            # CPU
            stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
            cpu = stdout.read().decode().strip()
            
            # Memory
            stdin, stdout, stderr = ssh.exec_command("free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'")
            memory = stdout.read().decode().strip()
            
            # Disk
            stdin, stdout, stderr = ssh.exec_command("df -h / | awk 'NR==2{print $5}' | cut -d'%' -f1")
            disk = stdout.read().decode().strip()
            
            ssh.close()
            
            return {
                'cpu': float(cpu) if cpu else 0,
                'memory': float(memory) if memory else 0,
                'disk': float(disk) if disk else 0,
                'status': 'online'
            }
        except Exception as e:
            return {'error': str(e), 'status': 'offline'}
