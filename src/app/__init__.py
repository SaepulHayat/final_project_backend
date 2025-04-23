from flask import Flask
from .config import config_by_name
import os


def create_app():
    config_name = os.getenv('FLASK_ENV', 'dev')
    app = Flask(__name__)
    app.config.from_object(config_by_name[config_name])
    
    @app.route('/')
    def index():
        return "setup flask is working!"
    
    return app