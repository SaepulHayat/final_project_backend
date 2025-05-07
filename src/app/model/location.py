# models/location.py
from ..extensions import db
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from .city import City

class Location(db.Model):
    """
    Represents a specific address or place, linked to a City.
    """
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    zip_code = db.Column(db.String(15), nullable=True, index=True)
    city_id = db.Column(db.Integer, db.ForeignKey('cities.id'), nullable=True, index=True)

    # --- Relationships ---
    city = db.relationship('City', back_populates='locations')
    users = db.relationship('User', back_populates='location', lazy='select')

    def __repr__(self):
        city_name = self.city.name if self.city else "Unknown City"
        return f'<Location id={self.id} address="{self.address}" city="{city_name}">'

    def to_dict(self):
        """Returns a dictionary representation of the location, including city/state/country."""
        city_obj = self.city
        state_obj = city_obj.state if city_obj else None
        country_obj = state_obj.country if state_obj else None

        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'zip_code': self.zip_code,
            'city_id': self.city_id,
            'city_name': city_obj.name if city_obj else None,
            'state_name': state_obj.name if state_obj else None,
            'country_name': country_obj.name if country_obj else None,
        }
