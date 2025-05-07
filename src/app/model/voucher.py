from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy import Numeric
from ..extensions import db

from typing import Optional, Dict, Union

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship
import secrets
import logging



class VoucherType:
    """Enum-like class untuk tipe voucher"""
    PERCENTAGE = 'percentage'
    FIXED_AMOUNT = 'fixed_amount'
    WELCOME = 'welcome'
    REFERRAL = 'referral'

class VoucherValidationError(Exception):
    """Custom exception untuk validasi voucher"""
    pass 

class Voucher(db.Model):
    """Model untuk manajemen voucher"""
    __tablename__ = 'vouchers'

    # Kolom identifikasi
    id = Column(Integer, primary_key=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(String(255))
    type = Column(String(50), nullable=False)
    value = Column(Numeric(10, 2), nullable=False)
    min_transaction = Column(Numeric(10, 2), default=Decimal('0'))
    max_discount = Column(Numeric(10, 2), nullable=True)
    is_active = Column(Boolean, default=True)
    start_date = Column(DateTime, default=datetime.utcnow)
    expired_date = Column(DateTime, nullable=False)

    # Penggunaan voucher
    usage_limit = Column(Integer, default=1)
    usage_count = Column(Integer, default=0)

    # Relasi transaksi
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    # used_transactions = relationship('Transaction', back_populates='applied_voucher')
    user = db.relationship('User', back_populates='vouchers')


    def __init__(self, *args, **kwargs):
        from src.app.model.user import User
        """
        Konstruktor dengan validasi tambahan
        """
        super().__init__(*args, **kwargs)
        self.validate_voucher_creation()

    def validate_voucher_creation(self):
        """
        Validasi saat pembuatan voucher
        """
        if self.value <= Decimal('0'):
            raise VoucherValidationError("Nilai voucher harus positif")
        
        if self.expired_date <= datetime.utcnow():
            raise VoucherValidationError("Tanggal kadaluarsa tidak valid")

    @classmethod
    def create_referral_voucher(
        cls, 
        user, 
        voucher_type: str = VoucherType.WELCOME
    ) -> 'Voucher':
        """
        Buat voucher otomatis untuk referral
        
        Args:
            user (User): Pengguna yang menerima voucher
            voucher_type (str): Tipe voucher
        
        Returns:
            Voucher: Voucher yang dibuat
        """
        voucher_configs: Dict[str, Dict[str, Union[str, Decimal, datetime]]] = {
            VoucherType.WELCOME: {
                'name': 'Voucher Selamat Datang',
                'description': 'Voucher spesial untuk member baru',
                'type': VoucherType.PERCENTAGE,
                'value': Decimal('10'),
                'min_transaction': Decimal('100000'),
                'expired_date': datetime.utcnow() + timedelta(days=30)
            },
            VoucherType.REFERRAL: {
                'name': 'Voucher Referral',
                'description': 'Bonus voucher dari kode referral',
                'type': VoucherType.FIXED_AMOUNT,
                'value': Decimal('50000'),
                'min_transaction': Decimal('200000'),
                'expired_date': datetime.utcnow() + timedelta(days=60)
            }
        }
        
        config = voucher_configs.get(
            voucher_type, 
            voucher_configs[VoucherType.WELCOME]
        )
        
        try:
            voucher = cls(
                code=cls._generate_voucher_code(),
                user=user,
                **config
            )
            
            db.session.add(voucher)
            return voucher
        
        except Exception as e:
            logging.error(f"Gagal membuat voucher: {e}")
            db.session.rollback()
            raise

    @classmethod
    def _generate_voucher_code(cls, length: int = 8) -> str:
        """
        Generate kode voucher unik
        
        Args:
            length (int): Panjang kode voucher
        
        Returns:
            str: Kode voucher unik
        """
        chars = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'
        max_attempts = 10

        for _ in range(max_attempts):
            code = ''.join(secrets.choice(chars) for _ in range(length))
            
            # Pastikan kode belum digunakan
            existing = cls.query.filter_by(code=code).first()
            if not existing:
                return code
        
        raise VoucherValidationError("Tidak dapat menghasilkan kode voucher unik")

    @property
    def is_expired(self) -> bool:
        """
        Cek apakah voucher sudah kadaluarsa
        
        Returns:
            bool: Status kadaluarsa voucher
        """
        return datetime.utcnow() > self.expired_date

    def is_valid(self, transaction_amount: Decimal) -> bool:
        """
        Cek validitas voucher
        
        Args:
            transaction_amount (Decimal): Jumlah transaksi
        
        Returns:
            bool: Apakah voucher masih valid
        """
        now = datetime.utcnow()
        
        return all([
            self.is_active,
            not self.is_expired,
            transaction_amount >= self.min_transaction,
            self.usage_count < self.usage_limit
        ])

    def apply_to_transaction(self, transaction):
        """
        Terapkan voucher ke transaksi
        
        Args:
            transaction (Transaction): Transaksi yang akan diberi voucher
        
        Returns:
            Decimal: Jumlah diskon
        
        Raises:
            VoucherValidationError: Jika voucher tidak valid
        """
        if not self.is_valid(transaction.total_amount):
            raise VoucherValidationError("Voucher tidak dapat digunakan")
        
        # Hitung diskon
        if self.type == VoucherType.PERCENTAGE:
            discount = transaction.total_amount * (self.value / Decimal('100'))
        else:
            discount = self.value
        
        # Terapkan batas maksimal diskon
        if self.max_discount:
            discount = min(discount, self.max_discount)
        
        # Update penggunaan voucher
        self.usage_count += 1
        if self.usage_count >= self.usage_limit:
            self.is_active = False
        
        return discount

    def __repr__(self) -> str:
        """
        Representasi string dari voucher
        
        Returns:
            str: Representasi voucher
        """
        return f"<Voucher {self.code} - {self.name}>"
