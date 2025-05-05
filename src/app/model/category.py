from ..extensions import db
from sqlalchemy import CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, func
from datetime import datetime, timezone
from .book_category_table import book_category_table


class Category(db.Model):
    __tablename__ = 'category'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False)

    books = db.relationship('Book', secondary=book_category_table, back_populates='categories')

    __table_args__ = (
        UniqueConstraint('name', name='uq_category_name'),
    )
    
    def to_dict(self, include_books=False): #For retrieveng and creating data. `include_books=True` is used when calling list of books that have corresponding category.
        """Returns a simple dictionary representation of the category."""
        data = {
            'id': self.id,
            'name': self.name
        }
        if include_books:
            data['books'] = [book.to_simple_dict() for book in self.books]
        return data
        

    def __repr__(self):
        return f'<Category {self.id}: {self.name}>'