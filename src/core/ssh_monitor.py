"""
SSH мониторинг удаленных серверов.
"""
import socket
import os
import tempfile
from io import StringIO

try:
    import paramiko
    SSH_AVAILABLE = True
except ImportError:
    SSH_AVAILABLE = False

class SSHMonitor:
    def __init__(self):
        self.available = SSH_AVAILABLE
    
    def _create_ssh_client(self, host, port=22, username='root', password=None, ssh_key_path=None, ssh_key_content=None):
        """Создание SSH клиента с различными методами аутентификации"""
        if not self.available:
            raise Exception('Paramiko не установлен')
        
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        # Настройки подключения
        connect_kwargs = {
            'hostname': host,
            'port': port,
            'username': username,
            'timeout': 10,
            'allow_agent': True,
            'look_for_keys': True
        }
        
        # Метод 1: SSH ключ из содержимого
        if ssh_key_content:
            try:
                # Создаем временный файл для ключа
                with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as tmp_key:
                    tmp_key.write(ssh_key_content)
                    tmp_key_path = tmp_key.name
                
                # Устанавливаем права доступа
                os.chmod(tmp_key_path, 0o600)
                
                # Загружаем ключ
                pkey = None
                for key_type in [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.DSSKey]:
                    try:
                        pkey = key_type.from_private_key_file(tmp_key_path)
                        break
                    except:
                        continue
                
                if pkey:
                    connect_kwargs['pkey'] = pkey
                
                # Удаляем временный файл
                os.unlink(tmp_key_path)
                
            except Exception as e:
                print(f"Ошибка загрузки ключа из содержимого: {e}")
        
        # Метод 2: SSH ключ из файла
        elif ssh_key_path and os.path.exists(ssh_key_path):
            try:
                pkey = None
                for key_type in [paramiko.RSAKey, paramiko.Ed25519Key, paramiko.ECDSAKey, paramiko.DSSKey]:
                    try:
                        pkey = key_type.from_private_key_file(ssh_key_path)
                        break
                    except:
                        continue
                
                if pkey:
                    connect_kwargs['pkey'] = pkey
                    
            except Exception as e:
                print(f"Ошибка загрузки ключа из файла: {e}")
        
        # Метод 3: Пароль
        elif password:
            connect_kwargs['password'] = password
        
        # Подключаемся
        ssh.connect(**connect_kwargs)
        return ssh
    
    def test_connection(self, host, port=22, username='root', password=None, ssh_key_path=None, ssh_key_content=None):
        """Тестирование SSH подключения"""
        if not self.available:
            return {'success': False, 'error': 'Paramiko не установлен'}
        
        try:
            ssh = self._create_ssh_client(host, port, username, password, ssh_key_path, ssh_key_content)
            
            # Тестовая команда
            stdin, stdout, stderr = ssh.exec_command('echo "SSH connection test successful"')
            result = stdout.read().decode().strip()
            error = stderr.read().decode().strip()
            
            ssh.close()
            
            if result:
                return {'success': True, 'message': 'SSH подключение успешно', 'test_output': result}
            else:
                return {'success': False, 'error': f'Ошибка выполнения команды: {error}'}
                
        except paramiko.AuthenticationException:
            return {'success': False, 'error': 'Ошибка аутентификации - неверные учетные данные'}
        except paramiko.SSHException as e:
            return {'success': False, 'error': f'SSH ошибка: {str(e)}'}
        except socket.timeout:
            return {'success': False, 'error': 'Тайм-аут подключения'}
        except socket.gaierror:
            return {'success': False, 'error': 'Не удается разрешить имя хоста'}
        except ConnectionRefusedError:
            return {'success': False, 'error': 'Подключение отклонено - SSH сервис недоступен'}
        except Exception as e:
            return {'success': False, 'error': f'Неожиданная ошибка: {str(e)}'}
    
    def get_metrics(self, host, port=22, username='root', password=None, ssh_key_path=None, ssh_key_content=None):
        """Получение метрик через SSH"""
        if not self.available:
            return {'error': 'Paramiko не установлен'}
        
        try:
            ssh = self._create_ssh_client(host, port, username, password, ssh_key_path, ssh_key_content)
            
            metrics = {}
            
            # CPU использование
            try:
                stdin, stdout, stderr = ssh.exec_command("top -bn1 | grep 'Cpu(s)' | awk '{print $2}' | cut -d'%' -f1")
                cpu_output = stdout.read().decode().strip()
                if not cpu_output:
                    # Альтернативная команда для CPU
                    stdin, stdout, stderr = ssh.exec_command("grep 'cpu ' /proc/stat | awk '{usage=($2+$4)*100/($2+$3+$4+$5)} END {print usage}'")
                    cpu_output = stdout.read().decode().strip()
                
                metrics['cpu'] = float(cpu_output) if cpu_output else 0
            except:
                metrics['cpu'] = 0
            
            # Использование памяти
            try:
                stdin, stdout, stderr = ssh.exec_command("free | grep Mem | awk '{printf \"%.1f\", $3/$2 * 100.0}'")
                memory_output = stdout.read().decode().strip()
                metrics['memory'] = float(memory_output) if memory_output else 0
            except:
                metrics['memory'] = 0
            
            # Использование диска
            try:
                stdin, stdout, stderr = ssh.exec_command("df -h / | awk 'NR==2{print $5}' | cut -d'%' -f1")
                disk_output = stdout.read().decode().strip()
                metrics['disk'] = float(disk_output) if disk_output else 0
            except:
                metrics['disk'] = 0
            
            # Дополнительная информация о системе
            try:
                stdin, stdout, stderr = ssh.exec_command("uname -a")
                system_info = stdout.read().decode().strip()
                metrics['system_info'] = system_info
            except:
                pass
            
            # Время работы системы
            try:
                stdin, stdout, stderr = ssh.exec_command("uptime")
                uptime = stdout.read().decode().strip()
                metrics['uptime'] = uptime
            except:
                pass
            
            ssh.close()
            
            metrics['status'] = 'online'
            return metrics
            
        except paramiko.AuthenticationException:
            return {'error': 'Ошибка аутентификации', 'status': 'offline'}
        except paramiko.SSHException as e:
            return {'error': f'SSH ошибка: {str(e)}', 'status': 'offline'}
        except socket.timeout:
            return {'error': 'Тайм-аут подключения', 'status': 'offline'}
        except socket.gaierror:
            return {'error': 'Не удается разрешить имя хоста', 'status': 'offline'}
        except ConnectionRefusedError:
            return {'error': 'Подключение отклонено', 'status': 'offline'}
        except Exception as e:
            return {'error': f'Ошибка: {str(e)}', 'status': 'offline'}
