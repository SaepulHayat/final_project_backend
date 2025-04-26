from datetime import datetime
from ..extensions import db

class Order(db.Model):
    """Model for the Order table."""
    __tablename__ = "orders"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    order_date = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    status = db.Column(db.String(50), nullable=False, default="pending") # CHECK constraint: valid statuses
    total_amount = db.Column(db.Numeric(12, 2), nullable=False) # CHECK constraint: >= 0
    shipping_address_id = db.Column(db.Integer, db.ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=True)
    billing_address_id = db.Column(db.Integer, db.ForeignKey("addresses.id", ondelete="RESTRICT"), nullable=True)
    shipping_method = db.Column(db.String(100), nullable=True)
    tracking_number = db.Column(db.String(100), nullable=True)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    user = db.relationship("User", back_populates="orders")
    shipping_address = db.relationship("Address", foreign_keys=[shipping_address_id], back_populates="shipping_orders")
    billing_address = db.relationship("Address", foreign_keys=[billing_address_id], back_populates="billing_orders")
    order_items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"Order({self.id}, User ID: {self.user_id}, Status: {self.status})"