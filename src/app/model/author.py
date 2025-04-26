from ..extensions import db

class Author(db.Model):
    """Model for the Authors table."""
    __tablename__ = "authors"

    author_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    author_name = db.Column(db.String(255), nullable=False)
    bio = db.Column(db.Text)

    # Relationships
    books = db.relationship('BookAuthor', backref='author')

    def __repr__(self):
        return f"Author(id={self.author_id}, name='{self.author_name}')"