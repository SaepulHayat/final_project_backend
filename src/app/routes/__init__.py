from .auth_route import auth_bp
from .author_route import author_bp
from .category_route import category_bp
from .publisher_route import publisher_bp
from .user_route import user_bp

__all__ = [
    'auth_bp',
    'author_bp',
    'category_bp',
    'publisher_bp',
    'user_bp'
]