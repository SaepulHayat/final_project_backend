from flask import Flask
from .config import config_by_name
from .extensions import init_db
from .model import *
from .routes import author_bp, book_bp, category_bp, publisher_bp, rating_bp
import os

from .seed import seed_db_command


def create_app():
    config_name = os.getenv('FLASK_ENV', 'dev')
    app = Flask(__name__)
    print("--- Config Name:", config_name) # Debug
    print("--- Keys in config_by_name:", config_by_name.keys())
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions here
    init_db(app)
    
    # Seed the database with initial data
    app.cli.add_command(seed_db_command)
    
    # Register blueprints
    app.register_blueprint(author_bp, url_prefix='/api/v1/authors')
    app.register_blueprint(book_bp, url_prefix='/api/v1/books')
    app.register_blueprint(category_bp, url_prefix='/api/v1/categories')
    app.register_blueprint(publisher_bp, url_prefix='/api/v1/publishers')
    app.register_blueprint(rating_bp)
        
    @app.route('/')
    def index():
        return "setup flask is working!"
    
    return app