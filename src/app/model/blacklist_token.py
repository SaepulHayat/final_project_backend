from datetime import datetime
from ..extensions import db

class BlacklistToken(db.Model):
    """Model for storing blacklisted JWT tokens."""
    __tablename__ = "blacklist_tokens"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    token = db.Column(db.String(500), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __init__(self, token):
        self.token = token

    def __repr__(self):
        return f"<BlacklistToken {self.token}>"