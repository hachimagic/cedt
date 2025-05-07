from flask import Flask, request
from flask_login import LoginManager, login_user
from .models.user import User

login_manager = LoginManager()

def create_app():
    app = Flask(__name__)
    from config import Config
    app.config.from_object(Config)
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB
    app.config['UPLOAD_FOLDER'] = 'uploads'
    app.config['ALLOWED_EXTENSIONS'] = {'pdf'}
    
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    with app.app_context():
        # Import and register blueprints
        from .routes.main import main_bp
        from .routes.auth import auth_bp
        from .routes.expenses import expenses_bp
        from .routes.debt import debt_bp
        from .routes.ai import ai_bp
        from .routes.settings import settings_bp
        
        app.register_blueprint(main_bp)
        app.register_blueprint(auth_bp)
        app.register_blueprint(expenses_bp, url_prefix='/expenses')
        app.register_blueprint(debt_bp)
        app.register_blueprint(ai_bp, url_prefix='/ai')
        app.register_blueprint(settings_bp)
        
        return app
