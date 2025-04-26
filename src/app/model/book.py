from datetime import datetime
from ..extensions import db

class Book(db.Model):
    """Model for the Books table."""
    __tablename__ = "books"

    book_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    isbn = db.Column(db.String(20), unique=True, nullable=False)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    publisher_id = db.Column(db.Integer, db.ForeignKey('publishers.publisher_id'))
    publication_date = db.Column(db.Date)
    language = db.Column(db.String(50))
    num_pages = db.Column(db.Integer)
    format = db.Column(db.String(50))
    cover_image_url = db.Column(db.String(255))

    # Relationships
    publisher = db.relationship('Publisher', backref='books')
    authors = db.relationship('BookAuthor', backref='book')
    genres = db.relationship('BookGenre', backref='book')
    listings = db.relationship('ProductListing', backref='book')
    reviews = db.relationship('Review', backref='book')

    def __repr__(self):
        return f"Book(id={self.book_id}, title='{self.title}', isbn='{self.isbn}')"