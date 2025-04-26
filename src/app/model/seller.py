from datetime import datetime
from ..extensions import db

class Seller(db.Model):
    """Model for the Seller table."""
    __tablename__ = "sellers"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    store_name = db.Column(db.String(255), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    user = db.relationship("User", back_populates="seller_profile")
    inventory = db.relationship("Inventory", back_populates="seller", cascade="all, delete-orphan")
    order_items = db.relationship("OrderItem", back_populates="seller")

    def __repr__(self):
        return f"Seller({self.id}, {self.store_name})"