# Remove this import if book_author_table is only used for the Author relationship
# from .book_author_table import book_author_table
from ..extensions import db
from sqlalchemy import CheckConstraint, ForeignKey, func # Add ForeignKey
from datetime import datetime, timezone
# Keep book_category_table import if needed for Category relationship
from .book_category_table import book_category_table


class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publisher.id'), nullable=True)
    description = db.Column(db.Text, nullable=True)
    rating = db.Column(db.Numeric(3, 2), nullable=True)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percent = db.Column(db.Integer, nullable=False, default=0)
    image_url_1 = db.Column(db.String(512), nullable=True)
    image_url_2 = db.Column(db.String(512), nullable=True)
    image_url_3 = db.Column(db.String(512), nullable=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('seller.id'), nullable=False)

    # Add the foreign key to the Author table
    author_id = db.Column(db.Integer, db.ForeignKey('author.id'), nullable=False) # <-- ADD THIS LINE

    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False)

    publisher = db.relationship('Publisher', back_populates='books')

    # Modify the relationship to Author (remove secondary, adjust back_populates)
    # authors = db.relationship('Author', secondary=book_author_table, back_populates='books') # <-- REMOVE THIS LINE
    author = db.relationship('Author', back_populates='books') # <-- ADD THIS LINE

    # Keep the Category relationship if it's still many-to-many
    categories = db.relationship('Category', secondary=book_category_table, back_populates='books')
    ratings = db.relationship('Rating', back_populates='book', cascade='all, delete-orphan')
    seller = db.relationship('Seller', back_populates='books')

    __table_args__ = (
        CheckConstraint('quantity >= 0', name='book_quantity_non_negative'),
        CheckConstraint('price > 0', name='book_price_positive'),
        CheckConstraint('discount_percent BETWEEN 0 AND 100', name='book_discount_percent_range'),
        db.Index('ix_book_title', 'title'),
        db.Index('ix_book_author_id', 'author_id') # <-- Optional: Add an index for the new foreign key
    )

    def __repr__(self):
         # Optionally update repr to include author
        return f'<Book {self.id}: {self.title} by Author {self.author_id}>'