from datetime import datetime
from ..extensions import db
from sqlalchemy import UniqueConstraint

class Review(db.Model):
    """Model for the Review table."""
    __tablename__ = "reviews"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # CHECK constraint: 1-5
    review_text = db.Column(db.Text, nullable=True)
    review_date = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    is_approved = db.Column(db.Boolean, default=False)

    book = db.relationship("Book", back_populates="reviews")
    user = db.relationship("User", back_populates="reviews")

    __table_args__ = (UniqueConstraint("book_id", "user_id"),)

    def __repr__(self):
        return f"Review({self.id}, Book ID: {self.book_id}, User ID: {self.user_id}, Rating: {self.rating})"