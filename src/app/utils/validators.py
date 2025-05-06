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


def validate_publisher_input(data: Dict[str, str], is_update: bool = False) -> Optional[Dict[str, str]]:
    """Validasi input untuk membuat atau memperbarui publisher."""
    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    name = data.get('name', '').strip()

    if not is_update or ('name' in data and name):
        if not name:
            errors['name'] = "Publisher name is required"
        elif len(name) > 255:
            errors['name'] = "Publisher name must not exceed 255 characters"

    return errors if errors else None

def validate_author_input(data: Dict[str, str], is_update: bool = False) -> Optional[Dict[str, str]]:
    """Validasi input untuk membuat atau memperbarui author."""
    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    full_name = data.get('full_name', '').strip()
    bio = data.get('bio', '').strip()

    if not is_update or ('full_name' in data and full_name):
        if not full_name:
            errors['full_name'] = "Full name is required"
        elif len(full_name) > 100: # Assuming a max length for full_name
            errors['full_name'] = "Full name must not exceed 100 characters"

    if 'bio' in data and len(bio) > 500: # Assuming a max length for bio
        errors['bio'] = "Bio must not exceed 500 characters"

    return errors if errors else None

def validate_category_input(data: Dict[str, str], is_update: bool = False) -> Optional[Dict[str, str]]:
    """Validasi input untuk membuat atau memperbarui category."""
    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    name = data.get('name', '').strip()

    # For create or if name is provided in update
    if not is_update or ('name' in data and name):
        if not name:
            errors['name'] = "Category name is required"
        elif len(name) > 100: # Matches model definition
            errors['name'] = "Category name must not exceed 100 characters"
    # If it's an update and 'name' is provided but empty after strip
    elif is_update and 'name' in data and not name:
        errors['name'] = "Category name cannot be empty"


    return errors if errors else None
def validate_rating_input(data: Dict[str, any], is_update: bool = False) -> Optional[Dict[str, str]]:
    """Validasi input untuk membuat atau memperbarui rating."""
    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    # Score validation
    if 'score' in data:
        score = data.get('score')
        if not isinstance(score, int):
            errors['score'] = "Score must be an integer"
        elif not (1 <= score <= 5):
            errors['score'] = "Score must be between 1 and 5"
    elif not is_update: # Score is required for create
        errors['score'] = "Score is required"

    # Text validation
    if 'text' in data:
        text = data.get('text')
        if text is not None: # Allow text to be explicitly set to None or empty string
            if not isinstance(text, str):
                errors['text'] = "Text must be a string"
            elif len(text) > 1000: # Max length for rating text
                errors['text'] = "Text must not exceed 1000 characters"

    return errors if errors else None
