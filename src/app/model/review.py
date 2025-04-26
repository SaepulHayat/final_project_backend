from datetime import datetime
from ..extensions import db

class Review(db.Model):
    """Model for the Reviews table."""
    __tablename__ = "reviews"

    review_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    review_text = db.Column(db.Text)
    review_date = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = db.relationship('User', backref='reviews')

    def __repr__(self):
        return f"Review(id={self.review_id}, book_id={self.book_id}, user_id={self.user_id}, rating={self.rating})"