from ..extensions import db

class OrderItem(db.Model):
    """Model for the OrderItem table."""
    __tablename__ = "order_items"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    inventory_id = db.Column(db.Integer, db.ForeignKey("inventory.id", ondelete="RESTRICT"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("books.id", ondelete="RESTRICT"), nullable=False)
    seller_id = db.Column(db.Integer, db.ForeignKey("sellers.id", ondelete="RESTRICT"), nullable=False)
    quantity = db.Column(db.Integer, nullable=False) # CHECK constraint: > 0
    price_per_item = db.Column(db.Numeric(10, 2), nullable=False)
    condition_at_purchase = db.Column(db.String(50), nullable=False)

    order = db.relationship("Order", back_populates="order_items")
    inventory_item = db.relationship("Inventory", back_populates="order_items")
    book = db.relationship("Book", back_populates="order_items")
    seller = db.relationship("Seller", back_populates="order_items")

    def __repr__(self):
        return f"OrderItem({self.id}, Order ID: {self.order_id}, Inventory ID: {self.inventory_id})"