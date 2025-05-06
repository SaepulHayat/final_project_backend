from ..extensions import db
from sqlalchemy import CheckConstraint, ForeignKey, func
from datetime import datetime, timezone
from .book_category_table import book_category_table
from .category import Category
from .author import Author
from .publisher import Publisher
from .user import User


class Book(db.Model):
    __tablename__ = 'book'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=True)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publisher.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
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

    # --- Relationships ---
    publisher = db.relationship('Publisher', back_populates='books')
    author = db.relationship('Author', back_populates='books')
    categories = db.relationship('Category', secondary=book_category_table, back_populates='books')
    ratings = db.relationship('Rating', back_populates='book', cascade='all, delete-orphan')
    user = db.relationship('User', back_populates='books_for_sale')

    # --- Table arguments (constraints and indexes) ---
    __table_args__ = (
        CheckConstraint('quantity >= 0', name='book_quantity_non_negative'),
        CheckConstraint('price > 0', name='book_price_positive'),
        CheckConstraint('discount_percent BETWEEN 0 AND 100', name='book_discount_percent_range'),

    )

    def get_seller_location_info(self):
        """Helper method to safely get seller's location details."""
        if not self.user or not self.user.location or not self.user.location.city:
            return None, None, None

        city = self.user.location.city
        state = city.state
        country = state.country if state else None

        return (
            city.name if city else None,
            state.name if state else None,
            country.name if country else None
        )


    def to_dict(self, include_categories=True):
        """Returns a detailed dictionary representation of the book."""
        city_name, state_name, country_name = self.get_seller_location_info()
        data = {
            'id': self.id,
            'title': self.title,
            'author_id': self.author_id,
            'author_name': self.author.full_name if self.author else None,
            'publisher_id': self.publisher_id,
            'publisher_name': self.publisher.name if self.publisher else None,
            'description': self.description,
            'rating': float(self.rating) if self.rating is not None else None,
            'quantity': self.quantity,
            'price': float(self.price) if self.price is not None else None, # Corrected price conversion
            'discount_percent': self.discount_percent,
            'user_name': self.user.full_name if self.user else None,
            'user_id': self.user_id,
            'seller_location': {
                            'city': city_name,
                            'state': state_name,
                            'country': country_name,
                        },
            'image_url_1': self.image_url_1,
            'image_url_2': self.image_url_2,
            'image_url_3': self.image_url_3,
            'created_at': self.created_at.isoformat() if self.created_at else None, # Added timestamp
            'updated_at': self.updated_at.isoformat() if self.updated_at else None, # Added timestamp
        }
        if include_categories and self.categories:
            # Corrected category serialization call
            data['categories'] = [category.to_dict() for category in self.categories]
        else:
            data['categories'] = []

        return data

    def to_simple_dict(self):
        """Returns a simpler dictionary representation of the book."""
        city_name, _, _ = self.get_seller_location_info() # Only need city for simple view
        return {
            'id': self.id,
            'title': self.title,
            'author_name': self.author.full_name if self.author else None,
            'image_url_1': self.image_url_1,
            'rating': float(self.rating) if self.rating is not None else None,
            'price': float(self.price) if self.price is not None else None, # Corrected price conversion
            'discount_percent': self.discount_percent,
            'user_name': self.user.full_name if self.user else None,
            'seller_city': city_name,
        }

    def __repr__(self):
        """Provide a developer-friendly string representation."""
        author_info = f"Author ID {self.author_id}" if self.author_id else "No Author"
        user_info = f"User ID {self.user_id}" if self.user_id else "No User"
        return f'<Book id={self.id} title="{self.title}" ({author_info}) ({user_info})>'