from flask import Flask
from flask_cors import CORS
from .config import config_by_name
from .extensions import init_extensions
from .model import user
from .router.auth_route import auth_bp
from .router.user_route import user_bp
import os


def create_app():
    config_name = os.getenv('FLASK_ENV', 'dev')
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions here
    init_extensions(app)
    
    # Initialize CORS
    CORS(app)

    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    
    
    @app.route('/')
    def index():
        return "setup flask is working!"
    
    return app