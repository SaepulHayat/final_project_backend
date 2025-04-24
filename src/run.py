import os
from app import create_app
from app.config import Config
from app.extensions import db
from app.model.user import User

app = create_app()

if __name__ == '__main__':
    app.run()
