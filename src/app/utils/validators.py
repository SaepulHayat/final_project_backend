import re
import logging
from .roles import UserRoles
from typing import Dict, Optional

logger = logging.getLogger(__name__)

def validate_email(email: str) -> bool:
    """Validasi format email sederhana."""
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_pattern, email) is not None

def validate_referral_code(referral_code: str) -> bool:
    """Validasi kode referral: 6 karakter, uppercase/angka, tidak kosong."""
    if not referral_code:
        return False
    if len(referral_code) != 6:
        logger.warning(f"Invalid referral code length: {len(referral_code)}")
        return False
    valid_chars = set('ACDEFGHJKLMNPQRSTUVWXYZ23456789')
    return all(char in valid_chars for char in referral_code)

def validate_password(password: str) -> Dict[str, str]:
    """Validasi kekuatan password dan panjangnya."""
    errors = {}
    if len(password) < 8:
        errors['password'] = "Password must be at least 8 characters"
    elif len(password) > 50:
        errors['password'] = "Password must not exceed 50 characters"
    elif not re.search(r'[A-Z]', password):
        errors['password'] = "Password must contain at least one uppercase letter"
    elif not re.search(r'[a-z]', password):
        errors['password'] = "Password must contain at least one lowercase letter"
    elif not re.search(r'\d', password):
        errors['password'] = "Password must contain at least one number"
    elif not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors['password'] = "Password must contain at least one special character"
    return errors

# validasi register input
def validate_register_input(data: Dict[str, str]) -> Optional[Dict[str, str]]:
    """Validasi seluruh input register user."""
    from ..model.user import User
    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    required_fields = ['full_name', 'email', 'password']
    for field in required_fields:
        if not data.get(field):
            errors[field] = f"{field.replace('_', ' ').title()} is required"

    if errors:
        return errors

    email = data['email'].strip().lower()
    if not validate_email(email):
        errors['email'] = "Invalid email format"

    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        errors['email'] = "Email already registered"

    role = data.get("role", UserRoles.CUSTOMER.value).lower()
    if not UserRoles.has_value(role):
        errors['role'] = f"Invalid role. Must be one of: {', '.join(UserRoles.values())}"

    full_name = data['full_name'].strip()
    if len(full_name) < 3:
        errors['full_name'] = "Full name must be at least 3 characters"
    elif len(full_name) > 80:
        errors['full_name'] = "Full name must not exceed 80 characters"

    password_errors = validate_password(data['password'])
    if password_errors:
        errors.update(password_errors)

    referred_by = data.get("referred_by", "").strip()
    if referred_by:
        logger.info(f"Validating referral code: {referred_by}")
        if not validate_referral_code(referred_by):
            errors['referred_by'] = "Invalid referral code format"
        else:
            referring_user = User.query.filter_by(referral_code=referred_by).first()
            if not referring_user:
                errors['referred_by'] = "Referral code not found"
            elif not referring_user.is_active:
                errors['referred_by'] = "Referral code is not active"
            if referring_user and referring_user.email == email:
                errors['referred_by'] = "You cannot use your own referral code"

    return errors if errors else None

# validasi login input
def validate_login_input(data: Dict[str, str]) -> Optional[Dict[str, str]]:
    """Validasi seluruh input login user."""
    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    required_fields = ['email', 'password']
    for field in required_fields:
        if not data.get(field):
            errors[field] = f"{field.replace('_', ' ').title()} is required"

    if 'email' in data:
        email = data['email'].strip().lower()
        if not validate_email(email):
            errors['email'] = "Invalid email format"

    if 'password' in data:
        password = data['password']
        password_errors = validate_password(password)
        if password_errors:
            errors.update(password_errors)

    return errors if errors else None

def validate_category_input(data: Dict[str, str], category_id: Optional[int] = None) -> Optional[Dict[str, str]]:
    """Validasi input untuk membuat atau memperbarui kategori."""
    from ..model.category import Category # Import here to avoid circular dependency
    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    name = data.get('name', '').strip()

    if not name:
        errors['name'] = "Category name is required"
    elif len(name) > 100:
        errors['name'] = "Category name must not exceed 100 characters"
    else:
        # Check uniqueness only if name is provided and valid so far
        # Note: Uniqueness check is also valuable here for immediate feedback,
        # but the service layer should perform the definitive check before commit.
        query = Category.query.filter(Category.name == name)
        if category_id: # Exclude self during update
            query = query.filter(Category.id != category_id)
        existing_category = query.first()
        if existing_category:
            errors['name'] = f"Category name '{name}' already exists"

    return errors if errors else None
