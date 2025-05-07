# models/city.py
from ..extensions import db
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

class City(db.Model):
    """
    Represents a city within a state.
    """
    __tablename__ = 'cities'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, index=True)
    state_id = db.Column(db.Integer, db.ForeignKey('states.id'), nullable=False, index=True)

    # --- Relationships ---
    state = db.relationship('State', back_populates='cities')
    locations = db.relationship('Location', back_populates='city', lazy='dynamic')

    def __repr__(self):
        state_name = self.state.name if self.state else "Unknown State"
        return f'<City id={self.id} name="{self.name}" state="{state_name}">'

    def to_dict(self):
        """Returns a dictionary representation of the city."""
        return {
            'id': self.id,
            'name': self.name,
            'state_id': self.state_id,
            'state_name': self.state.name if self.state else None,
            'country_name': self.state.country.name if self.state and self.state.country else None # Access country via state
        }
