from ..extensions import db
from sqlalchemy import CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, func
from datetime import datetime, timezone

book_author_table = db.Table('book_author',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('author_id', db.Integer, db.ForeignKey('author.id'), primary_key=True)
)

book_category_table = db.Table('book_category',
    db.Column('book_id', db.Integer, db.ForeignKey('book.id'), primary_key=True),
    db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
)

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
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False)

    publisher = db.relationship('Publisher', back_populates='books')
    authors = db.relationship('Author', secondary=book_author_table, back_populates='books')
    categories = db.relationship('Category', secondary=book_category_table, back_populates='books')
    ratings = db.relationship('Rating', back_populates='book', cascade='all, delete-orphan')
    seller = db.relationship('Seller', back_populates='books')

    __table_args__ = (
        CheckConstraint('quantity >= 0', name='book_quantity_non_negative'),
        CheckConstraint('price > 0', name='book_price_positive'),
        CheckConstraint('discount_percent BETWEEN 0 AND 100', name='book_discount_percent_range'),
        db.Index('ix_book_title', 'title'),
    )

    def __repr__(self):
        return f'<Book {self.id}: {self.title}>'

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

    def __repr__(self):
        return f'<Category {self.id}: {self.name}>'