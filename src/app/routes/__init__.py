from .auth_route import auth_bp
from .user_route import user_bp
from .category_route import category_bp
from .book_route import book_bp

__all__ = [
    'auth_bp',
    'category_bp',
    'user_bp',
    'book_bp'
]