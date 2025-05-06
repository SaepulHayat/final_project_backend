from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime
from ..extensions import db
<<<<<<< HEAD
from ..util.security import hash_password, verify_password, generate_referral_code
=======
from ..utils.security import hash_password, verify_password, generate_referral_code
>>>>>>> origin/product-db

class User(db.Model):
    __tablename__ = 'users'

<<<<<<< HEAD
    id = Column(Integer, primary_key=True)
    full_name = Column(String(100), nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default='customer', nullable=False)
    balance = Column(Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    referral_code = Column(String(6), unique=True, nullable=False)
    referred_by = Column(Integer, ForeignKey('users.id'), nullable=True)
    total_referred = Column(Integer, default=0, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    vouchers = relationship('Voucher', back_populates='user')
    

    referrer = relationship(
=======
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), default='customer', nullable=False)
    balance = db.Column(db.Numeric(10, 2), default=Decimal('0.00'), nullable=False)
    referral_code = db.Column(db.String(6), unique=True, nullable=False)
    referred_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    total_referred = db.Column(db.Integer, default=0, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True, index=True)

    # --- Relationships ---
    vouchers = db.relationship('Voucher', back_populates='user')
    location = db.relationship('Location', back_populates='users', foreign_keys=[location_id])
    books_for_sale = db.relationship('Book', back_populates='user', lazy='dynamic', cascade="all, delete-orphan")
    ratings = db.relationship('Rating', back_populates='user', cascade="all, delete-orphan")
    location_id = db.Column(db.Integer, db.ForeignKey('locations.id'), nullable=True)
    referrer = db.relationship(
>>>>>>> origin/product-db
        'User',
        remote_side=[id],
        back_populates='referred_users',
        foreign_keys=[referred_by]
    )
<<<<<<< HEAD
    
    referred_users = relationship(
=======

    referred_users = db.relationship(
>>>>>>> origin/product-db
        'User',
        back_populates='referrer',
        foreign_keys=[referred_by]
    )

    def __init__(self, full_name, email, password=None, role='customer', **kwargs):
        self.full_name = full_name
        self.email = email.lower()
        self.role = role
        self.referral_code = generate_referral_code()
        if password:
            self.password = password
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def password(self):
        raise AttributeError('Password is not readable')

    @password.setter
    def password(self, password):
        self.password_hash = hash_password(password)

    def verify_password(self, password):
        return verify_password(self.password_hash, password)

<<<<<<< HEAD
    def to_dict(self):
        return {
=======
    def to_dict(self, include_location=False):
        data = {
>>>>>>> origin/product-db
            'id': self.id,
            'full_name': self.full_name,
            'email': self.email,
            'role': self.role,
            'referral_code': self.referral_code,
            'balance': float(self.balance) if self.balance is not None else 0,
            'is_active': self.is_active,
            'total_referred': self.total_referred,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
<<<<<<< HEAD
=======
        if include_location and self.location:
            data['location'] = self.location.to_dict()
        elif self.location:
            data['city_name'] = self.location.city.name if self.location.city else None

        return data
>>>>>>> origin/product-db

    def update_last_login(self):
        self.last_login = datetime.utcnow()

    def add_balance(self, amount: Decimal):
        if amount <= Decimal('0'):
            raise ValueError("Jumlah saldo harus positif")
        self.balance += amount

    def deduct_balance(self, amount: Decimal):
        if amount <= Decimal('0'):
            raise ValueError("Jumlah penarikan harus positif")
        if self.balance < amount:
            raise ValueError("Saldo tidak mencukupi")
        self.balance -= amount