from ..extensions import db
from datetime import datetime

class Wishlist(db.Model):
    __tablename__ = 'wishlists'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False, index=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    
    # --- Relationships ---
    user = db.relationship('User', backref=db.backref('wishlists', lazy='dynamic', cascade='all, delete-orphan'))
    book = db.relationship('Book', backref=db.backref('wishlists', lazy='dynamic'))
    
    # --- Table arguments (constraints) ---
    __table_args__ = (
        db.UniqueConstraint('user_id', 'book_id', name='uq_wishlist_user_book'),
    )
    
    def __init__(self, user_id, book_id):
        self.user_id = user_id
        self.book_id = book_id
    
    def to_dict(self):
        """Returns a dictionary representation of the wishlist item."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'book': self.book.to_dict() if self.book else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        """Provide a developer-friendly string representation."""
        return f'<Wishlist id={self.id} user_id={self.user_id} book_id={self.book_id}>'
