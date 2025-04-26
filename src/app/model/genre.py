from ..extensions import db

class Genre(db.Model):
    """Model for the Genres table."""
    __tablename__ = "genres"

    genre_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    genre_name = db.Column(db.String(100), unique=True, nullable=False)

    # Relationships
    books = db.relationship('BookGenre', backref='genre')

    def __repr__(self):
        return f"Genre(id={self.genre_id}, name='{self.genre_name}')"