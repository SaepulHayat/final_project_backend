import os
from src.app import create_app
from src.app.config import Config
from src.app.extensions import db
from src.app.model import *

app = create_app()

if __name__ == '__main__':
    app.run()
