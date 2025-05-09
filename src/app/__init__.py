import logging
from flask import Flask
from flask_cors import CORS
import click
from flask.cli import AppGroup
from .config import config_by_name
from .extensions import init_extensions
from .model import *
from .routes import author_bp, category_bp, publisher_bp, city_bp, auth_bp, user_bp, state_bp, country_bp, location_bp, book_bp, cart_bp, wishlist_bp
from .routes.transaction_route import transaction_bp
from .routes.rating_route import book_ratings_bp, user_ratings_bp, ratings_bp
from .seed import seed_all, clear_data 
import os


def create_app():
    config_name = os.getenv('FLASK_ENV', 'prod')
    app = Flask(__name__)
    logging.basicConfig(level=logging.INFO) # Configure logging to show INFO level messages
    print("--- Config Name:", config_name) # Debug
    print("--- Keys in config_by_name:", config_by_name.keys())
    app.config.from_object(config_by_name[config_name])
    
    init_extensions(app)

    CORS(app)

    # Define the seed CLI group
    # seed_cli = AppGroup('seed', help='Commands for seeding the database.')

    # @seed_cli.command('run')
    # def run_seed_command():
    #     """Seeds the database with initial data."""
    #     # No need for app.app_context() here as Flask CLI handles it
    #     try:
    #         seed_all()
    #         click.echo("Database seeded successfully.")
    #     except Exception as e:
    #         # db.session.rollback() # seed_all or individual seeders should handle rollback on error
    #         click.echo(f"Error during seeding: {e}")
    #         # raise # Optionally re-raise

    # @seed_cli.command('clear')
    # @click.option('--really', is_flag=True, help="Confirms the operation. Data will be lost.")
    # def clear_db_data_command(really):
    #     """Clears data from relevant tables."""
    #     if not really:
    #         click.echo("Operation aborted. Use --really to confirm data deletion.")
    #         return
    #     try:
    #         clear_data()
    #         click.echo("Database data cleared successfully.")
    #     except Exception as e:
    #         # db.session.rollback() # clear_data should handle rollback
    #         click.echo(f"Error during data clearing: {e}")
    #         # raise

    # app.cli.add_command(seed_cli)
    
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
    app.register_blueprint(wishlist_bp, url_prefix='/api/v1/wishlists')
    app.register_blueprint(cart_bp, url_prefix='/api/v1/carts')
    app.register_blueprint(transaction_bp, url_prefix='/api/v1/transactions')
    
    @app.route('/')
    def index():
        return "setup flask is working!"
    
    return app
