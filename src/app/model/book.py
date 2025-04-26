from datetime import datetime
from ..extensions import db
from .author import book_authors
from .category import book_categories

class Book(db.Model):
    """The core model for abstract book metadata."""
    __tablename__ = "books"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(20), nullable=False, unique=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    publisher_id = db.Column(db.Integer, db.ForeignKey("publishers.id", ondelete="SET NULL"), nullable=True)
    publication_date = db.Column(db.Date, nullable=True)
    num_pages = db.Column(db.Integer, nullable=True) # CHECK constraint: > 0
    language_code = db.Column(db.String(10), db.ForeignKey("languages.language_code", ondelete="SET NULL"), nullable=True)
    cover_image_url = db.Column(db.String(512), nullable=True)
    average_rating = db.Column(db.Numeric(3, 2), default=0.00) # CHECK constraint: 0-5
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    publisher = db.relationship("Publisher", back_populates="books")
    language = db.relationship("Language")
    authors = db.relationship("Author", secondary=book_authors, back_populates="books")
    categories = db.relationship("Category", secondary=book_categories, back_populates="books")
    inventory_items = db.relationship("Inventory", back_populates="book", cascade="all, delete-orphan")
    reviews = db.relationship("Review", back_populates="book", cascade="all, delete-orphan")
    order_items = db.relationship("OrderItem", back_populates="book")

    def __repr__(self):
        return f"Book({self.id}, {self.title}, {self.isbn})"