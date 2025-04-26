from datetime import datetime
from ..extensions import db

class Publisher(db.Model):
    """Model for the Publisher table."""
    __tablename__ = "publishers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(255), nullable=False, unique=True)
    contact_email = db.Column(db.String(255), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    books = db.relationship("Book", back_populates="publisher")

    def __repr__(self):
        return f"Publisher({self.id}, {self.name})"