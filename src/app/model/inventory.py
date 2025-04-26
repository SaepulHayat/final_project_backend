from datetime import datetime
from ..extensions import db
from sqlalchemy import UniqueConstraint

class Inventory(db.Model):
    """Model for the Inventory table."""
    __tablename__ = "inventory"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("sellers.id", ondelete="CASCADE"), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False) # CHECK constraint: >= 0
    quantity = db.Column(db.Integer, nullable=False, default=0) # CHECK constraint: >= 0
    condition = db.Column(db.String(50), default="New") # CHECK constraint: valid conditions
    condition_description = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now())
    updated_at = db.Column(db.DateTime(timezone=True), server_default=db.func.now(), onupdate=db.func.now())

    book = db.relationship("Book", back_populates="inventory_items")
    seller = db.relationship("Seller", back_populates="inventory")
    order_items = db.relationship("OrderItem", back_populates="inventory_item")

    __table_args__ = (UniqueConstraint("book_id", "seller_id", "condition"),)

    def __repr__(self):
        return f"Inventory({self.id}, Book ID: {self.book_id}, Seller ID: {self.seller_id})"