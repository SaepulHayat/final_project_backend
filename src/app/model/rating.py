from ..extensions import db
from sqlalchemy import CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, func
from datetime import datetime, timezone

class Rating(db.Model):
    __tablename__ = 'rating'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False)
    score = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False)

    user = db.relationship('User', back_populates='ratings')
    book = db.relationship('Book', back_populates='ratings')

    __table_args__ = (
        CheckConstraint('score BETWEEN 1 AND 5', name='rating_score_range'),
        db.Index('ix_rating_user_id', 'user_id'),
        db.Index('ix_rating_book_id', 'book_id'),
    )
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'book_id': self.book_id,
            'score': self.score,
            'text': self.text,
        }

    def __repr__(self):
        return f'<Rating {self.id} by User {self.user_id} for Book {self.book_id} - Score: {self.score}>'