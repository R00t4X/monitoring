#!/bin/bash

# Список файлов для удаления
rm -f admin.py
rm -f advanced_monitor.py  
rm -f alert_system.py
rm -f models.py
rm -f auto_setup.py
rm -f setup_and_run.py
rm -f start.py
rm -f run.py
rm -f quick_start.py
rm -f check_sensitive.py
rm -f install.sh
rm -f install.bat
rm -f git_prepare.sh
rm -f install_and_run.sh

# Удаление неиспользуемых директорий
rm -rf app/
rm -rf config/
rm -rf migrations/
rm -rf tests/
rm -rf scripts/

echo "✅ Неиспользуемые файлы удалены"
