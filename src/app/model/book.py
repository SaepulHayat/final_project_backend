from ..extensions import db
from sqlalchemy import CheckConstraint
from datetime import datetime

from .category import Category
from .user import User

class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    
    author_name = db.Column(db.String(255), nullable=True)
    publisher_name = db.Column(db.String(255), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    user_name = db.Column(db.String(255), nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    category = db.relationship('Category', back_populates='books')

    description = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Numeric(3, 2), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=0)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percent = db.Column(db.Integer, nullable=False, default=0)
    
    image_url_1 = db.Column(db.String(512), nullable=True)
    image_url_2 = db.Column(db.String(512), nullable=True)
    image_url_3 = db.Column(db.String(512), nullable=True)
    
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), server_onupdate=db.func.now(), nullable=False)

    user = db.relationship('User', back_populates='books_for_sale')

    __table_args__ = (
        CheckConstraint('quantity >= 0', name='book_quantity_non_negative'),
        CheckConstraint('price > 0', name='book_price_positive'),
        CheckConstraint('discount_percent BETWEEN 0 AND 100', name='book_discount_percent_range'),
    )

    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'author_name': self.author_name,
            'publisher_name': self.publisher_name,
            'user_name': self.user_name,
            'user_id': self.user_id,
            'category_id': self.category_id,
            'category': self.category.to_dict() if self.category else None,
            'description': self.description,
            'rating': float(self.rating) if self.rating else None,
            'quantity': self.quantity,
            'price': float(self.price),
            'discount_percent': self.discount_percent,
            'image_url_1': self.image_url_1,
            'image_url_2': self.image_url_2,
            'image_url_3': self.image_url_3,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
        }

    def __repr__(self):
        return f'<Book {self.id} "{self.title}" by {self.author_name}>'
