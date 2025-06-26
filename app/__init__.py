"""
Основной модуль приложения.
Создание и конфигурация Flask-приложения.
"""
from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager

# Создаем экземпляры расширений
db = SQLAlchemy()
migrate = Migrate()
socketio = SocketIO()
login_manager = LoginManager()

def create_app(config_name='development'):
    """Создание и настройка экземпляра Flask-приложения."""
    app = Flask(__name__, 
                template_folder='../templates',
                static_folder='../static')
    
    # Загрузка конфигурации
    from config.settings import config_by_name
    app.config.from_object(config_by_name[config_name])
    
    # Инициализация расширений
    db.init_app(app)
    migrate.init_app(app, db)
    socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    
    # Настройка аутентификации
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'
    
    # Регистрация blueprints
    from app.controllers.main import main as main_blueprint
    from app.controllers.auth import auth as auth_blueprint
    from app.controllers.admin import admin as admin_blueprint
    from app.controllers.api import api as api_blueprint
    
    app.register_blueprint(main_blueprint)
    app.register_blueprint(auth_blueprint, url_prefix='/auth')
    app.register_blueprint(admin_blueprint, url_prefix='/admin')
    app.register_blueprint(api_blueprint, url_prefix='/api')
    
    # Обработчики ошибок
    register_error_handlers(app)
    
    return app

def register_error_handlers(app):
    """Регистрация обработчиков ошибок."""
    from flask import render_template, jsonify, request
    
    @app.errorhandler(404)
    def page_not_found(e):
        if request.path.startswith('/api'):
            return jsonify(error="Not found"), 404
        return render_template('errors/404.html'), 404
        
    @app.errorhandler(500)
    def internal_server_error(e):
        if request.path.startswith('/api'):
            return jsonify(error="Internal server error"), 500
        return render_template('errors/500.html'), 500
