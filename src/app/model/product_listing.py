from ..extensions import db

class ProductListing(db.Model):
    """Model for the Inventory/ProductListings table."""
    __tablename__ = "product_listings"

    listing_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    book_id = db.Column(db.Integer, db.ForeignKey('books.book_id'), nullable=False)
    store_id = db.Column(db.Integer, db.ForeignKey('stores.store_id'), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_percentage = db.Column(db.Numeric(5, 2), default=0.0)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    sku = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    # Composite unique constraint for sku and store_id
    __table_args__ = (db.UniqueConstraint('sku', 'store_id', name='_sku_store_uc'),)

    def __repr__(self):
        return f"ProductListing(id={self.listing_id}, book_id={self.book_id}, store_id={self.store_id}, price={self.price})"