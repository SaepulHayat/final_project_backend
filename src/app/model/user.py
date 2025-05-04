from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey, Numeric
from sqlalchemy.orm import relationship
from decimal import Decimal
from datetime import datetime
from ..extensions import db
from ..utils.security import hash_password, verify_password, generate_referral_code

class User(db.Model):
    __tablename__ = 'users'

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
    seller_profile = relationship('Seller', back_populates='user', uselist=False, cascade="all, delete-orphan")
    

    referrer = relationship(
        'User',
        remote_side=[id],
        back_populates='referred_users',
        foreign_keys=[referred_by]
    )
    
    referred_users = relationship(
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

    def to_dict(self):
        return {
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