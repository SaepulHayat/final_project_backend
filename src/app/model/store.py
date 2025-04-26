from ..extensions import db

class Store(db.Model):
    """Model for the Stores table."""
    __tablename__ = "stores"

    store_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    store_name = db.Column(db.String(255), nullable=False)
    location = db.Column(db.Text)

    # Relationships
    listings = db.relationship('ProductListing', backref='store')

    def __repr__(self):
        return f"Store(id={self.store_id}, name='{self.store_name}')"