from flask import Flask
from .config import config_by_name
from .extensions import init_db
from .model import *
from .routes import author_bp, category_bp, publisher_bp, city_bp, auth_bp, user_bp, state_bp, country_bp, location_bp, book_bp
from .routes.rating_route import book_ratings_bp, user_ratings_bp, ratings_bp
import os


def create_app():
    config_name = os.getenv('FLASK_ENV', 'dev')
    app = Flask(__name__)
    print("--- Config Name:", config_name) # Debug
    print("--- Keys in config_by_name:", config_by_name.keys())
    app.config.from_object(config_by_name[config_name])
    
    init_db(app)

    # @app.cli.command("seed-db")
    # def seed_db_command_cli():
    #     """Seeds the database with sample data."""
    #     from .seed import seed_all
    #     seed_all()
    #     print("Database seeding initiated via app.cli command.")
    
    # Register blueprints
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(user_bp, url_prefix='/api/v1/users')
    app.register_blueprint(author_bp, url_prefix='/api/v1/authors')
    app.register_blueprint(category_bp, url_prefix='/api/v1/categories')
    app.register_blueprint(publisher_bp, url_prefix='/api/v1/publishers')
    app.register_blueprint(city_bp, url_prefix='/api/v1/cities')
    app.register_blueprint(state_bp, url_prefix='/api/v1/states')
    app.register_blueprint(book_bp, url_prefix='/api/v1/books')
    app.register_blueprint(book_ratings_bp)
    app.register_blueprint(user_ratings_bp)
    app.register_blueprint(ratings_bp)
    app.register_blueprint(country_bp, url_prefix='/api/v1/countries')
    app.register_blueprint(location_bp, url_prefix='/api/v1/locations')

    @app.route('/')
    def index():
        return "setup flask is working!"
    
    return app