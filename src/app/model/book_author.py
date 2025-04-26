from ..extensions import db

class BookAuthor(db.Model):
    """Model for the BookAuthors linking table."""
    __tablename__ = "book_authors"

    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey('authors.author_id'), primary_key=True)

    def __repr__(self):
        return f"BookAuthor(book_id={self.book_id}, author_id={self.author_id})"