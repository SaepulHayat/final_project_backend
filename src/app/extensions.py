import string
from flask_sqlalchemy import SQLAlchemy  
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from flask_bcrypt import Bcrypt

db = SQLAlchemy()  
migrate = Migrate()
jwt = JWTManager()
bcrypt = Bcrypt()

def init_extensions(app):
    db.init_app(app)  
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)