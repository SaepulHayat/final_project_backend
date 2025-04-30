from .author_views import author_bp
from .book_views import book_bp
from .category_views import category_bp
from .publisher_views import publisher_bp
from .rating_views import rating_bp

all_views = [
    author_bp,
    book_bp,
    category_bp,
    publisher_bp,
    rating_bp,
]