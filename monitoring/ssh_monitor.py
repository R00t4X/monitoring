"""
SSH мониторинг удаленных серверов.
"""
import os
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
    
    # ...existing code...

# Глобальный экземпляр SSH монитора
ssh_monitor = SSHMonitor()
