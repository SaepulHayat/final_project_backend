from ..extensions import db
from sqlalchemy import CheckConstraint, func
from datetime import datetime, timezone

class Author(db.Model):
    __tablename__ = 'author'

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False)

    books = db.relationship('Book', back_populates='author', lazy='dynamic')

    def to_dict(self, include_books=False):
        """Returns a detailed dictionary representation of the author."""
        data = {
            'id': self.id,
            'full_name': self.full_name,
            'bio': self.bio,
        }
        
        if include_books:
            data['books'] = [book.to_simple_dict() for book in self.books.all()]
        return data

    def __repr__(self):
        return f'<Author {self.id}: {self.full_name}>'