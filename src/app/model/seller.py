from ..extensions import db
from sqlalchemy import CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, func
from datetime import datetime, timezone

class Seller(db.Model):
    __tablename__ = 'seller'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    name = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False)

    user = db.relationship('User', back_populates='seller_profile')
    books = db.relationship('Book', back_populates='seller')

    def __repr__(self):
        return f'<Seller {self.id}: {self.name} (User ID: {self.user_id})>'
