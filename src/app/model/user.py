from datetime import datetime
from sqlalchemy import CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, func
from ..extensions import db


from datetime import datetime
from sqlalchemy import CheckConstraint, PrimaryKeyConstraint, UniqueConstraint, func
from ..extensions import db

class User(db.Model):
    """Table for user information."""
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=0.0)
    referral_code = db.Column(db.String(10), unique=True, nullable=False)
    referred_by = db.Column(db.String(10), nullable=True)
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = db.Column(db.DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False)

    seller_profile = db.relationship('Seller', back_populates='user', uselist=False, cascade='all, delete-orphan')
    ratings = db.relationship('Rating', back_populates='user', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return f"User({self.id}, {self.username}, {self.email}, Role: {self.role})"