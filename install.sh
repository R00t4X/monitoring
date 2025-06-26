#!/bin/bash

echo "=================================================="
echo "🚀 АВТОУСТАНОВКА СИСТЕМЫ МОНИТОРИНГА (Linux/macOS)"
echo "=================================================="

# Проверка Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 не найден! Установите Python 3.7 или выше"
    exit 1
fi

echo "✅ Python3 найден: $(python3 --version)"

# Проверка pip
if ! command -v pip3 &> /dev/null; then
    echo "❌ pip3 не найден! Установите pip для Python3"
    exit 1
fi

echo "✅ pip3 найден"

# Запуск Python скрипта установки
echo "🔧 Запуск автоматической установки..."
python3 setup_and_run.py

echo "✅ Установка завершена!"
