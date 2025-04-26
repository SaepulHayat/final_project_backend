from ..extensions import db

class BookGenre(db.Model):
    """Model for the BookGenres linking table."""
    __tablename__ = "book_genres"

    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), primary_key=True)
    genre_id = db.Column(db.Integer, db.ForeignKey('genres.genre_id'), primary_key=True)

    def __repr__(self):
        return f"BookGenre(book_id={self.book_id}, genre_id={self.genre_id})"