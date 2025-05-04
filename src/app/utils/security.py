from flask_bcrypt import Bcrypt
import secrets
import logging
from sqlalchemy.exc import SQLAlchemyError
from ..extensions import bcrypt

logger = logging.getLogger(__name__)

def hash_password(password: str) -> str:
    """Hash password dengan Flask-Bcrypt."""
    return bcrypt.generate_password_hash(password).decode('utf-8')

def verify_password(hashed_password: str, password: str) -> bool:
    """Verifikasi password dengan Flask-Bcrypt."""
    return bcrypt.check_password_hash(hashed_password, password)

def generate_referral_code(length=6, max_attempts=10) -> str:
    """Generate kode referral unik."""
    from ..model.user import User
    chars = 'ACDEFGHJKLMNPQRSTUVWXYZ23456789'
    for attempt in range(max_attempts):
        try:
            code = ''.join(secrets.choice(chars) for _ in range(length))
            if len(code) != length:
                logger.warning(f"Generated code length mismatch: {len(code)} vs {length}")
                continue
            existing_code = User.query.filter_by(referral_code=code).first()
            if not existing_code:
                logger.info(f"Generated unique referral code: {code}")
                return code
            logger.info(f"Referral code already exists, retrying: {code}")
        except SQLAlchemyError as e:
            logger.error(f"Database error during referral code generation: {e}")
            continue
        except Exception as e:
            logger.error(f"Unexpected error in referral code generation: {e}")
            continue
    error_msg = f"Failed to generate unique {length}-character referral code after {max_attempts} attempts"
    logger.error(error_msg)
    raise ValueError(error_msg)

def generate_secure_token(length=32) -> str:
    """Generate token aman untuk berbagai keperluan."""
    return secrets.token_hex(length // 2)
