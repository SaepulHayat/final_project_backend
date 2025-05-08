from ..extensions import db
from sqlalchemy import CheckConstraint
from datetime import datetime

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    transaction_code = db.Column(db.String(20), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    book_id = db.Column(db.Integer, db.ForeignKey('book.id'), nullable=False, index=True)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('pending', 'paid', 'processing', 'shipped', 'delivered', 'cancelled', 'refunded', name='transaction_status'), default='pending')
    payment_method = db.Column(db.String(50), nullable=False)
    shipping_location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    shipping_phone = db.Column(db.String(20), nullable=True)
    shipping_notes = db.Column(db.Text, nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), server_onupdate=db.func.now(), nullable=False)
    
    # --- Relationships ---
    customer = db.relationship('User', foreign_keys=[customer_id], backref='purchases')
    seller = db.relationship('User', foreign_keys=[seller_id], backref='sales')
    book = db.relationship('Book', backref='transactions')
    shipping_location = db.relationship('Location', backref='shipping_transactions')
    
    # --- Table arguments (constraints) ---
    __table_args__ = (
        CheckConstraint('quantity > 0', name='transaction_quantity_positive'),
        CheckConstraint('amount > 0', name='transaction_amount_positive'),
    )
    
    def __init__(self, customer_id, seller_id, book_id, amount, quantity=1, payment_method='balance', **kwargs):
        self.customer_id = customer_id
        self.seller_id = seller_id
        self.book_id = book_id
        self.amount = amount
        self.quantity = quantity
        self.payment_method = payment_method
        self.transaction_code = self._generate_transaction_code()
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def _generate_transaction_code(self):
        import random
        import string
        prefix = "TRX"
        random_part = ''.join(random.choices(string.digits, k=10))
        return f"{prefix}{random_part}"
    
    def to_dict(self):
        """Returns a dictionary representation of the transaction."""
        result = {
            'id': self.id,
            'transaction_code': self.transaction_code,
            'customer_id': self.customer_id,
            'customer_name': self.customer.full_name if self.customer else None,
            'seller_id': self.seller_id,
            'seller_name': self.seller.full_name if self.seller else None,
            'book_id': self.book_id,
            'book_title': self.book.title if self.book else None,
            'book_image': self.book.image_url_1 if self.book else None,
            'quantity': self.quantity,
            'amount': float(self.amount) if self.amount is not None else None,
            'status': self.status,
            'payment_method': self.payment_method,
            'tracking_number': self.tracking_number,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
        
        if self.shipping_location:
            result['shipping_address'] = self.shipping_location.to_dict()
            result['shipping_phone'] = self.shipping_phone
            result['shipping_notes'] = self.shipping_notes
            
        return result
        
    def __repr__(self):
        """Provide a developer-friendly string representation."""
        return f'<Transaction id={self.id} code="{self.transaction_code}" customer_id={self.customer_id} seller_id={self.seller_id} status={self.status}>'
