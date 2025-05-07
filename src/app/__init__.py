from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
import os

from .config import config_by_name
from .extensions import init_extensions, db 
from .model import *
from .routes import book_bp, category_bp, auth_bp, user_bp
from .seed import seed_db_command

def create_app():
    config_name = os.getenv('FLASK_ENV', 'development')
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    # Init SQLAlchemy, JWT, etc.
    init_extensions(app)
    
    # Enable CORS
    CORS(app)
    
    # Enable DB migrations
    Migrate(app, db)  # <-- required for `flask db`

    # CLI seed command
    app.cli.add_command(seed_db_command)
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(user_bp, url_prefix='/user')
    app.register_blueprint(category_bp, url_prefix='/api/v1/categories')
    app.register_blueprint(book_bp, url_prefix='/api/v1/books') 
    
    @app.route('/')
    def index():
        return "Setup Flask is Working!"
    
    with app.app_context():
        from . import model
        db.create_all()  # Optional if you use migrations

    return app
