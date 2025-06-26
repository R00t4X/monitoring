#!/usr/bin/env python3
"""
Простой запуск системы мониторинга без сложных зависимостей.
"""
import os
import sys

def main():
    """Запуск упрощенного приложения."""
    print("🚀 ЗАПУСК УПРОЩЕННОЙ СИСТЕМЫ МОНИТОРИНГА")
    print("=" * 45)
    
    try:
        # Импортируем и запускаем упрощенное приложение
        from simple_app import app
        
        host = "127.0.0.1"
        port = 5000
        
        print(f"🌐 Приложение будет доступно по адресу: http://{host}:{port}")
        print("🛑 Для остановки нажмите Ctrl+C")
        print("=" * 45)
        
        app.run(host=host, port=port, debug=True)
        
    except ImportError as e:
        print(f"❌ Ошибка импорта: {e}")
        print("📦 Убедитесь, что установлен Flask: pip install Flask")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    main()
