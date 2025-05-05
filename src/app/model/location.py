# models/location.py
from ..extensions import db
from sqlalchemy.orm import relationship

class Location(db.Model):
    __tablename__ = 'locations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=True)
    address = db.Column(db.String(255), nullable=True)
    zip_code = db.Column(db.String(15), nullable=True, unique=True)
    city = db.Column(db.String(50), nullable=True, unique=True)
    state = db.Column(db.String(50), nullable=True, unique=True)

    # --- Relationships ---
    users = db.relationship('User', back_populates='location', lazy='dynamic')

    def __repr__(self):
        return f'<Location id={self.id} name="{self.name}">'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'zip_code': self.zip_code,
            'city': self.city,
            'state': self.state,
        }