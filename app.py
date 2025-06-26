from flask import Flask, render_template, jsonify
import os

# Создание экземпляра Flask приложения
app = Flask(__name__)

# Базовая конфигурация
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')
app.config['DEBUG'] = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

# Основные маршруты
@app.route('/')
def index():
    """Главная страница"""
    return render_template('index.html')

@app.route('/api/health')
def health_check():
    """Эндпоинт проверки здоровья"""
    return jsonify({
        'статус': 'здоров',
        'сообщение': 'Приложение работает'
    })

@app.route('/api/status')
def status():
    """Эндпоинт статуса для мониторинга"""
    return jsonify({
        'приложение': 'мониторинг',
        'версия': '1.0.0',
        'статус': 'активно'
    })

# Обработчики ошибок
@app.errorhandler(404)
def not_found(error):
    return jsonify({'ошибка': 'Страница не найдена'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'ошибка': 'Внутренняя ошибка сервера'}), 500

if __name__ == '__main__':
    # Запуск приложения
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    print(f"🚀 Запуск приложения мониторинга на {host}:{port}")
    app.run(
        host=host,
        port=port,
        debug=app.config['DEBUG']
    )
