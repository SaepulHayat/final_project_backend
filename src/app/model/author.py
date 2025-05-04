from ..extensions import db
from sqlalchemy import CheckConstraint, func
from datetime import datetime, timezone

class Author(db.Model):
    __tablename__ = 'author'

    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=True)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False)

    books = db.relationship('Book', back_populates='author', lazy='dynamic')

    def __repr__(self):
        return f'<Author {self.id}: {self.first_name} {self.last_name}>'