import os
from dotenv import load_dotenv

load_dotenv()

basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'my_very_secret_key')
    DEBUG = False

class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.getenv('DEV_DATABASE_URL', 'sqlite:///' + os.path.join(basedir, 'dev.db'))
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class ProductionConfig(Config):
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///prod.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
class TestConfig(Config):  
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'  
    SQLALCHEMY_TRACK_MODIFICATIONS = False  
    TESTING = True  

config_by_name = {
    'dev': DevelopmentConfig,
    'prod': ProductionConfig,
}