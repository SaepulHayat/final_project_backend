# models/country.py
from ..extensions import db
from sqlalchemy.orm import relationship

class Country(db.Model):
    """
    Represents a country.
    """
    __tablename__ = 'countries'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False, index=True)
    code = db.Column(db.String(10), unique=True, nullable=True) # Optional country code (e.g., ID, US)

    # --- Relationships ---
    states = db.relationship('State', back_populates='country', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Country id={self.id} name="{self.name}">'

    def to_dict(self):
        """Returns a dictionary representation of the country."""
        return {
            'id': self.id,
            'name': self.name,
            'code': self.code
        }
