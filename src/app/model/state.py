# models/state.py
from ..extensions import db
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class State(db.Model):
    """
    Represents a state or province within a country.
    """
    __tablename__ = 'states'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    country_id = db.Column(db.Integer, db.ForeignKey('countries.id'), nullable=False, index=True)

    # --- Relationships ---
    country = db.relationship('Country', back_populates='states')
    cities = db.relationship('City', back_populates='state', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        country_name = self.country.name if self.country else "Unknown Country"
        return f'<State id={self.id} name="{self.name}" country="{country_name}">'

    def to_dict(self):
        """Returns a dictionary representation of the state."""
        return {
            'id': self.id,
            'name': self.name,
            'country_id': self.country_id,
            'country_name': self.country.name if self.country else None
        }
