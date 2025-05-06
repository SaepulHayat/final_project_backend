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

def validate_city_input(data: Dict[str, any], is_update: bool = False) -> Optional[Dict[str, str]]:
    """Validasi input untuk membuat atau memperbarui city."""
    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    name = data.get('name', '').strip()
    state_id = data.get('state_id')

    # Name validation
    if not is_update or ('name' in data and name):
        if not name:
            errors['name'] = "City name is required"
        elif len(name) > 100: # Matches model definition
            errors['name'] = "City name must not exceed 100 characters"
    elif is_update and 'name' in data and not name:
        errors['name'] = "City name cannot be empty"

    # State ID validation
    if not is_update or ('state_id' in data and state_id is not None):
        if state_id is None:
            errors['state_id'] = "State ID is required"
        elif not isinstance(state_id, int):
            errors['state_id'] = "State ID must be an integer"
        # Further validation (checking if state_id exists in DB) is done in the service layer

    return errors if errors else None

def validate_state_input(data: Dict[str, any], is_update: bool = False) -> Optional[Dict[str, str]]:
    """Validasi input untuk membuat atau memperbarui state."""
    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    name = data.get('name', '').strip()
    country_id = data.get('country_id')

    # Name validation
    if not is_update or ('name' in data and name):
        if not name:
            errors['name'] = "State name is required"
        elif len(name) > 100: # Matches model definition
            errors['name'] = "State name must not exceed 100 characters"
    elif is_update and 'name' in data and not name:
        errors['name'] = "State name cannot be empty"

    # Country ID validation
    if not is_update or ('country_id' in data and country_id is not None):
        if country_id is None:
            errors['country_id'] = "Country ID is required"
        elif not isinstance(country_id, int):
            errors['country_id'] = "Country ID must be an integer"
        # Further validation (checking if country_id exists in DB) is done in the service layer

    return errors if errors else None

def validate_country_input(data: Dict[str, str], is_update: bool = False) -> Optional[Dict[str, str]]:
    """Validasi input untuk membuat atau memperbarui country."""
    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    name = data.get('name', '').strip()
    code = data.get('code', '').strip() if data.get('code') is not None else None

    # Name validation
    if not is_update or ('name' in data and name):
        if not name:
            errors['name'] = "Country name is required"
        elif len(name) > 100: # Matches model definition
            errors['name'] = "Country name must not exceed 100 characters"
    elif is_update and 'name' in data and not name:
        errors['name'] = "Country name cannot be empty"

    # Code validation (optional but validated if provided)
    if 'code' in data and code is not None and not code: # if "code": ""
         errors['code'] = "Country code cannot be an empty string if provided, or omit the key to keep it unchanged/null."
    elif code is not None and len(code) > 10: # Matches model definition
         errors['code'] = "Country code must not exceed 10 characters"


    return errors if errors else None
def validate_location_input(data: Dict[str, any], is_update: bool = False) -> Optional[Dict[str, str]]:
    """Validasi input untuk membuat atau memperbarui location."""
    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    city_id = data.get('city_id')
    address = data.get('address', '').strip()
    zip_code = data.get('zip_code', '').strip()
    name = data.get('name', '').strip()

    # city_id validation
    if not is_update or ('city_id' in data and city_id is not None):
        if city_id is None:
            errors['city_id'] = "City ID is required"
        elif not isinstance(city_id, int):
            errors['city_id'] = "City ID must be an integer"
        # Existence check is done in the service layer

    # address validation
    if not is_update or ('address' in data and address):
        if not address and not is_update: # Address is required for create, but optional for update if not provided
             errors['address'] = "Address is required for creation"
        elif address and len(address) > 255: # Matches model definition
            errors['address'] = "Address must not exceed 255 characters"
    elif is_update and 'address' in data and not address: # Allow setting address to empty string/None on update
         pass # Handled by service layer normalization

    # zip_code validation
    if 'zip_code' in data and zip_code and len(zip_code) > 15: # Matches model definition
        errors['zip_code'] = "Zip code must not exceed 15 characters"
    elif is_update and 'zip_code' in data and not zip_code: # Allow setting zip_code to empty string/None on update
         pass # Handled by service layer normalization


    # name validation
    if 'name' in data and name and len(name) > 100: # Matches model definition
        errors['name'] = "Name must not exceed 100 characters"
    elif is_update and 'name' in data and not name: # Allow setting name to empty string/None on update
         pass # Handled by service layer normalization


    return errors if errors else None

def validate_book_input(data: Dict[str, any], is_update: bool = False) -> Optional[Dict[str, str]]:
    """Validasi input untuk membuat atau memperbarui book."""
    from ..model.author import Author
    from ..model.publisher import Publisher
    from ..model.category import Category
    from decimal import Decimal

    errors: Dict[str, str] = {}

    if not data:
        return {"general": "No data provided"}

    # Required fields for creation
    if not is_update:
        required_fields = ['title', 'price', 'quantity']
        for field in required_fields:
            if field not in data or data.get(field) is None:
                errors[field] = f"{field.replace('_', ' ').title()} is required"

    # Validate fields if they are present in data (for both create and update)
    if 'title' in data:
        title = data.get('title', '').strip()
        if not title and not is_update:
             errors['title'] = "Title is required for creation"
        elif title and len(title) > 255:
            errors['title'] = "Title must not exceed 255 characters"
        elif is_update and 'title' in data and not title:
             errors['title'] = "Title cannot be empty"


    if 'description' in data:
        description = data.get('description')
        if description is not None and not isinstance(description, str):
             errors['description'] = "Description must be a string or null"


    if 'price' in data:
        price = data.get('price')
        if price is None and not is_update:
             errors['price'] = "Price is required for creation"
        elif price is not None:
            try:
                price_decimal = Decimal(str(price))
                if price_decimal <= 0:
                    errors['price'] = "Price must be a positive number"
            except:
                errors['price'] = "Price must be a valid number"


    if 'quantity' in data:
        quantity = data.get('quantity')
        if quantity is None and not is_update:
             errors['quantity'] = "Quantity is required for creation"
        elif quantity is not None:
            if not isinstance(quantity, int):
                errors['quantity'] = "Quantity must be an integer"
            elif quantity < 0:
                errors['quantity'] = "Quantity must be a non-negative integer"


    if 'discount_percent' in data:
        discount_percent = data.get('discount_percent')
        if discount_percent is not None:
            if not isinstance(discount_percent, int):
                errors['discount_percent'] = "Discount percent must be an integer"
            elif not (0 <= discount_percent <= 100):
                errors['discount_percent'] = "Discount percent must be between 0 and 100"


    if 'author_id' in data and data['author_id'] is not None:
        author_id = data['author_id']
        if not isinstance(author_id, int):
            errors['author_id'] = "Author ID must be an integer"
        else:
            # Check if author exists
            if not Author.query.get(author_id):
                errors['author_id'] = f"Author with ID {author_id} not found."

    if 'publisher_id' in data and data['publisher_id'] is not None:
        publisher_id = data['publisher_id']
        if not isinstance(publisher_id, int):
            errors['publisher_id'] = "Publisher ID must be an integer"
        else:
            # Check if publisher exists
            if not Publisher.query.get(publisher_id):
                errors['publisher_id'] = f"Publisher with ID {publisher_id} not found."

    if 'category_ids' in data and data['category_ids'] is not None:
        category_ids = data['category_ids']
        if not isinstance(category_ids, list):
            errors['category_ids'] = "Category IDs must be a list of integers"
        else:
            # Check if all category IDs are integers and exist
            valid_category_ids = []
            for cat_id in category_ids:
                if not isinstance(cat_id, int):
                    errors['category_ids'] = "Category IDs must be a list of integers"
                    break
                valid_category_ids.append(cat_id)

            if 'category_ids' not in errors and valid_category_ids:
                 categories = Category.query.filter(Category.id.in_(valid_category_ids)).all()
                 if len(categories) != len(set(valid_category_ids)):
                     found_ids = {cat.id for cat in categories}
                     missing_ids = [cid for cid in valid_category_ids if cid not in found_ids]
                     errors['category_ids'] = f"Categories with IDs {missing_ids} not found."
            elif 'category_ids' not in errors and not valid_category_ids and category_ids:
                 # Case where category_ids is an empty list, which is valid
                 pass
            elif 'category_ids' not in errors and not category_ids and 'category_ids' in data:
                 # Case where category_ids is explicitly provided as empty list
                 pass


    # Image URL validations (optional, just check type if provided)
    if 'image_url_1' in data and data['image_url_1'] is not None and not isinstance(data['image_url_1'], str):
        errors['image_url_1'] = "Image URL 1 must be a string or null"
    if 'image_url_2' in data and data['image_url_2'] is not None and not isinstance(data['image_url_2'], str):
        errors['image_url_2'] = "Image URL 2 must be a string or null"
    if 'image_url_3' in data and data['image_url_3'] is not None and not isinstance(data['image_url_3'], str):
        errors['image_url_3'] = "Image URL 3 must be a string or null"


    return errors if errors else None
