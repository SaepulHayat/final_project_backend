from ..extensions import db
from sqlalchemy import CheckConstraint
from datetime import datetime

class Cart(db.Model):
    __tablename__ = 'carts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), server_onupdate=db.func.now(), nullable=False)
    
    # --- Relationships ---
    user = db.relationship('User', backref=db.backref('cart_items', lazy='dynamic', cascade='all, delete-orphan'))
    book = db.relationship('Book', backref=db.backref('cart_items', lazy='dynamic'))
    
    # --- Table arguments (constraints) ---
    __table_args__ = (
        db.UniqueConstraint('user_id', 'book_id', name='uq_cart_user_book'),
        CheckConstraint('quantity > 0', name='cart_quantity_positive'),
    )
    
    def __init__(self, user_id, book_id, quantity=1):
        self.user_id = user_id
        self.book_id = book_id
        self.quantity = quantity
    
    def to_dict(self):
        """Returns a dictionary representation of the cart item."""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'book_id': self.book_id,
            'book': self.book.to_dict() if self.book else None,
            'quantity': self.quantity,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        """Provide a developer-friendly string representation."""
        return f'<Cart id={self.id} user_id={self.user_id} book_id={self.book_id} quantity={self.quantity}>'
