# models/location.py
from ..extensions import db
from sqlalchemy.orm import relationship

class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    address = db.Column(db.String(255), nullable=True)
    zip_code = db.Column(db.Integer(10), nullable=True)
    city = db.Column(db.String(50), nullable=True)
    state = db.Column(db.String(50), nullable=True)

    # --- Relationships ---
    users = db.relationship('User', back_populates='location', lazy='dynamic')

    def __repr__(self):
        return f'<Location id={self.id} name="{self.name}">'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'city': self.city,
            'country': self.country,
            # Add other fields to the dictionary representation
        }