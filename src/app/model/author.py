from datetime import datetime
from ..extensions import db

# Association table for Book and Author (Many-to-Many)
book_authors = db.Table(
    "book_authors",
    db.Column("book_id", db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), primary_key=True),
    db.Column("author_id", db.Integer, db.ForeignKey("authors.id", ondelete="CASCADE"), primary_key=True),
)

class Author(db.Model):
    """Model for the Author table."""
    __tablename__ = "authors"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    first_name = db.Column(db.String(100), nullable=True)
    last_name = db.Column(db.String(100), nullable=False)
    bio = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    books = db.relationship("Book", secondary=book_authors, back_populates="authors")

    def __repr__(self):
        return f"Author({self.id}, {self.first_name} {self.last_name})"