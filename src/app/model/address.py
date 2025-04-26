from datetime import datetime
from ..extensions import db

class Address(db.Model):
    """Model for the Address table."""
    __tablename__ = "addresses"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    address_type = db.Column(db.String(20), nullable=False) # CHECK constraint: 'shipping' or 'billing'
    street_address = db.Column(db.String(255), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    state_province = db.Column(db.String(100), nullable=True)
    postal_code = db.Column(db.String(20), nullable=False)
    country = db.Column(db.String(100), nullable=False)
    is_default = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    user = db.relationship("User", back_populates="addresses")
    shipping_orders = db.relationship("Order", foreign_keys="Order.shipping_address_id", back_populates="shipping_address")
    billing_orders = db.relationship("Order", foreign_keys="Order.billing_address_id", back_populates="billing_address")

    def __repr__(self):
        return f"Address({self.id}, {self.street_address}, {self.city})"