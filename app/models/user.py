"""
Модель пользователя для аутентификации и авторизации.
"""
import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, login_manager

class Role(db.Model):
    """Роль пользователя."""
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer, default=0)
    
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    # Определение прав доступа
    MONITOR = 1      # Просмотр данных мониторинга
    MANAGE = 2       # Управление серверами
    ALERT = 4        # Управление оповещениями
    ADMIN = 8        # Административные права
    
    @staticmethod
    def insert_roles():
        """Создание базовых ролей."""
        roles = {
            'user': [Role.MONITOR],
            'operator': [Role.MONITOR, Role.MANAGE],
            'admin': [Role.MONITOR, Role.MANAGE, Role.ALERT, Role.ADMIN]
        }
        
        default_role = 'user'
        
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            
            role.permissions = sum(roles[r])
            role.default = (role.name == default_role)
            db.session.add(role)
        
        db.session.commit()
    
    def __repr__(self):
        return f'<Role {self.name}>'

class User(UserMixin, db.Model):
    """Пользователь системы."""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True, nullable=False)
    username = db.Column(db.String(64), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(128))
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    
    # Дополнительные поля
    last_login = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        return self.role is not None and (self.role.permissions & permission) == permission
    
    def is_admin(self):
        return self.has_permission(Role.ADMIN)
    
    def __repr__(self):
        return f'<User {self.username}>'

@login_manager.user_loader
def load_user(user_id):
    """Загрузка пользователя по ID для flask-login."""
    return User.query.get(int(user_id))
