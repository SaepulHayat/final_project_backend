# Remove this import if book_author_table is only used for the Author relationship
# from .book_author_table import book_author_table
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

    # Modify the relationship to Book (remove secondary, adjust back_populates)
    # books = db.relationship('Book', secondary=book_author_table, back_populates='authors') # <-- REMOVE THIS LINE
    books = db.relationship('Book', back_populates='author', cascade='all, delete-orphan', lazy='dynamic') # <-- ADD THIS LINE
    # 'cascade' ensures books are deleted if the author is deleted.
    # 'lazy=dynamic' allows querying the books collection.

    def __repr__(self):
        return f'<Author {self.id}: {self.first_name} {self.last_name}>'