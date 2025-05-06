import os
<<<<<<< HEAD
from src.app import create_app
from src.app.config import Config
from src.app.extensions import db


import logging

logging.basicConfig(level=logging.DEBUG) 
=======
from app import create_app
from app.config import Config
from app.extensions import db
from app.model import *
>>>>>>> origin/product-db

app = create_app()

if __name__ == '__main__':
    app.run()
