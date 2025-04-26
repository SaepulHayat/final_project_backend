from datetime import datetime
from ..extensions import db

# Association table for Book and Category (Many-to-Many)
book_categories = db.Table(
    "book_categories",
    db.Column("book_id", db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    db.Column("category_id", db.Integer, db.ForeignKey("categories.id", ondelete="CASCADE"), primary_key=True),
)

class Category(db.Model):
    """Model for the Category table."""
    __tablename__ = "categories"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    parent_category_id = db.Column(db.Integer, db.ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    parent = db.relationship("Category", remote_side=[id], back_populates="children")
    children = db.relationship("Category", back_populates="parent")
    books = db.relationship("Book", secondary=book_categories, back_populates="categories")

    def __repr__(self):
        return f"Category({self.id}, {self.name})"