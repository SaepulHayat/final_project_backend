# src/app/views/book_views.py

from flask import Blueprint, request, jsonify, g, abort
from decimal import Decimal, InvalidOperation
# Assuming decorators are defined elsewhere and populate g.user
# from ..auth.decorators import login_required, role_admin, role_seller, roles_required
# Placeholder decorators for demonstration
def login_required(f):
    return f

def login_required(f): return f
def role_admin(f): return f
def role_seller(f): return f
def roles_required(f): return f



# Import necessary Flask-SQLAlchemy components and models
from ..extensions import db
from ..model.book import Book
from ..model.category import Category
from ..model.author import Author
from ..model.publisher import Publisher
from ..model.seller import Seller
from ..model.user import User # Needed for g.user simulation / real auth
from sqlalchemy import distinct # Needed for distinct results when joining multiple many-to-many
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload # For eager loading details

# Create Blueprint
book_bp = Blueprint('book_bp', __name__, url_prefix='/api/v1/books')

# --- Helper Serialization Functions ---

def serialize_author_summary(author):
    return {
        "id": author.id,
        "name": f"{author.first_name} {author.last_name or ''}".strip()
    }

def serialize_category_summary(category):
    return {"id": category.id, "name": category.name}

def serialize_publisher_summary(publisher):
     return {"id": publisher.id, "name": publisher.name} if publisher else None

def serialize_seller_summary(seller):
    return {
        "id": seller.id,
        "name": seller.name,
        "location": seller.location
    } if seller else None

def serialize_rating_summary(rating):
     return {
         "id": rating.id,
         "user_id": rating.user_id,
         # "username": rating.user.username, # Add if needed, requires join/load
         "score": rating.score,
         "text": rating.text,
         "created_at": rating.created_at.isoformat()
     }

def serialize_book_list_item(book):
     """Serializer for list view (less detail)."""
     return {
        "id": book.id,
        "title": book.title,
        "price": str(book.price),
        "discount_percent": book.discount_percent,
        "rating": float(book.rating) if book.rating is not None else None,
        "quantity": book.quantity,
        "seller_id": book.seller_id,
        "image_url_1": book.image_url_1,
        # Eager load these in the query if performance is critical for lists
        "authors": [serialize_author_summary(a) for a in book.authors],
        "categories": [serialize_category_summary(c) for c in book.categories],
        "publisher": serialize_publisher_summary(book.publisher),
     }

def serialize_book_detail(book):
    """Serializer for detail view (more detail)."""
    return {
        "id": book.id,
        "title": book.title,
        "description": book.description,
        "price": str(book.price),
        "discount_percent": book.discount_percent,
        "rating": float(book.rating) if book.rating is not None else None,
        "quantity": book.quantity,
        "image_url_1": book.image_url_1,
        "image_url_2": book.image_url_2,
        "image_url_3": book.image_url_3,
        "created_at": book.created_at.isoformat(),
        "updated_at": book.updated_at.isoformat(),
        # Include related objects
        "authors": [serialize_author_summary(a) for a in book.authors],
        "categories": [serialize_category_summary(c) for c in book.categories],
        "publisher": serialize_publisher_summary(book.publisher),
        "seller": serialize_seller_summary(book.seller),
        # Optionally include ratings - might need separate endpoint if many
        # "ratings": [serialize_rating_summary(r) for r in book.ratings] # Can be slow if many ratings
    }


# --- Book Model Endpoints ---

# POST /api/v1/books/ (Seller, Admin)
@book_bp.route('/', methods=['POST'])
@login_required
@roles_required('Seller', 'Admin')
def add_book_listing():
    """
    Add a new book listing.
    Requires title, price, quantity. Optional: description, discount_percent,
    publisher_id, author_ids (list), category_ids (list), image urls.
    If user is Seller, seller_id is set automatically.
    If user is Admin, seller_id must be provided in the request.
    """
    data = request.get_json()
    if not data:
        abort(400, description="No data provided.")

    # --- Validation ---
    required_fields = ['title', 'price', 'quantity']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        abort(400, description=f"Missing required fields: {', '.join(missing_fields)}")

    try:
        price = Decimal(data['price'])
        quantity = int(data['quantity'])
        discount = int(data.get('discount_percent', 0))
        if price <= 0 or quantity < 0 or not (0 <= discount <= 100):
            raise ValueError("Invalid numeric value.")
    except (ValueError, TypeError, InvalidOperation):
        abort(400, description="Invalid format for price, quantity, or discount_percent.")

    # --- Determine Seller ID ---
    seller_id = None
    if g.user.role == 'Seller':
        seller = Seller.query.filter_by(user_id=g.user.id).first()
        if not seller:
            # This case should ideally not happen if user creation/role assignment is correct
            abort(403, description="Seller profile not found for the current user.")
        seller_id = seller.id
    elif g.user.role == 'Admin':
        seller_id = data.get('seller_id')
        if seller_id is None:
            abort(400, description="Admin must provide 'seller_id' when creating a book.")
        # Check if the provided seller_id exists
        if not Seller.query.get(seller_id):
            abort(404, description=f"Seller with ID {seller_id} not found.")

    # --- Fetch Related Entities (Assume IDs are provided and valid) ---
    authors = []
    if 'author_ids' in data:
        try:
            author_ids = [int(aid) for aid in data['author_ids']]
            authors = Author.query.filter(Author.id.in_(author_ids)).all()
            if len(authors) != len(author_ids):
                 abort(404, description="One or more specified authors not found.")
        except (ValueError, TypeError):
             abort(400, description="Invalid format for author_ids list.")

    categories = []
    if 'category_ids' in data:
        try:
            category_ids = [int(cid) for cid in data['category_ids']]
            categories = Category.query.filter(Category.id.in_(category_ids)).all()
            if len(categories) != len(category_ids):
                 abort(404, description="One or more specified categories not found.")
        except (ValueError, TypeError):
             abort(400, description="Invalid format for category_ids list.")

    publisher = None
    publisher_id = data.get('publisher_id')
    if publisher_id is not None:
        try:
            publisher = Publisher.query.get(int(publisher_id))
            if not publisher:
                abort(404, description=f"Publisher with ID {publisher_id} not found.")
        except (ValueError, TypeError):
             abort(400, description="Invalid format for publisher_id.")

    # --- Create Book ---
    new_book = Book(
        title=data['title'],
        description=data.get('description'),
        price=price,
        quantity=quantity,
        discount_percent=discount,
        image_url_1=data.get('image_url_1'),
        image_url_2=data.get('image_url_2'),
        image_url_3=data.get('image_url_3'),
        seller_id=seller_id,
        publisher=publisher # Assign publisher object directly
    )

    # Append authors and categories
    new_book.authors.extend(authors)
    new_book.categories.extend(categories)

    try:
        db.session.add(new_book)
        db.session.commit()
        # Use the detail serializer for the response of a newly created item
        return jsonify(serialize_book_detail(new_book)), 201
    except IntegrityError as e:
        db.session.rollback()
        print(f"Integrity Error on book creation: {e}") # Log the error
        abort(500, description="Database error occurred while adding the book.")
    except Exception as e:
        db.session.rollback()
        print(f"Unexpected Error on book creation: {e}") # Log the error
        abort(500, description="An unexpected error occurred.")


# GET /api/v1/books/ (Guest, User, Seller, Admin) - WITH FILTERING
@book_bp.route('/', methods=['GET'])
def list_books():
    """
    List all books (paginated, filterable, searchable). Public listing.
    [Docstring with query parameters remains the same as previous version]
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # --- Filtering ---
    # Eager load relationships commonly needed for the list serialization
    query = Book.query.options(
        joinedload(Book.authors),
        joinedload(Book.categories),
        joinedload(Book.publisher)
    )
    needs_distinct = False # Flag to add distinct() if needed

    # Search (Title and Description)
    search_term = request.args.get('search', None, type=str)
    if search_term:
        query = query.filter(
            Book.title.ilike(f'%{search_term}%') |
            Book.description.ilike(f'%{search_term}%')
        )

    # Category Filter (Many-to-Many)
    category_ids_str = request.args.get('categories', None, type=str)
    if category_ids_str:
        try:
            category_ids = [int(cat_id.strip()) for cat_id in category_ids_str.split(',') if cat_id.strip()]
            if category_ids:
                # Use relationship for filtering
                query = query.filter(Book.categories.any(Category.id.in_(category_ids)))
                # No join needed here, but might need distinct if combined with other many-to-many filters using .any()
                # needs_distinct = True # Usually not needed with .any() unless complex joins happen elsewhere
        except ValueError:
            abort(400, description="Invalid category ID format. Please provide comma-separated integers.")

    # Author Filter (Many-to-Many)
    author_ids_str = request.args.get('authors', None, type=str)
    if author_ids_str:
        try:
            author_ids = [int(auth_id.strip()) for auth_id in author_ids_str.split(',') if auth_id.strip()]
            if author_ids:
                 # Use relationship for filtering
                query = query.filter(Book.authors.any(Author.id.in_(author_ids)))
                # needs_distinct = True # Usually not needed with .any()
        except ValueError:
            abort(400, description="Invalid author ID format. Please provide comma-separated integers.")

    # Publisher Filter (Foreign Key)
    publisher_id = request.args.get('publisher_id', None, type=int)
    if publisher_id is not None:
        query = query.filter(Book.publisher_id == publisher_id)

    # Price Filter
    min_price_str = request.args.get('min_price', None, type=str)
    max_price_str = request.args.get('max_price', None, type=str)
    try:
        if min_price_str is not None:
            min_price = Decimal(min_price_str)
            query = query.filter(Book.price >= min_price)
        if max_price_str is not None:
            max_price = Decimal(max_price_str)
            query = query.filter(Book.price <= max_price)
    except InvalidOperation:
        abort(400, description="Invalid price format. Please provide a valid number.")

    # Rating Filter
    min_rating_str = request.args.get('min_rating', None, type=str)
    if min_rating_str is not None:
        try:
            min_rating = Decimal(min_rating_str)
            if 0 <= min_rating <= 5:
                 # Filter on the rating column, ensuring it's not NULL
                 query = query.filter(Book.rating != None, Book.rating >= min_rating)
            else:
                 abort(400, description="min_rating must be between 0 and 5.")
        except InvalidOperation:
            abort(400, description="Invalid rating format. Please provide a valid number.")

    # Location Filter (via Seller)
    location = request.args.get('location', None, type=str)
    if location:
        # Explicit join needed here
        query = query.join(Book.seller).filter(Seller.location.ilike(f'%{location}%'))
        # Joining Seller (one-to-many from Book's perspective) doesn't usually require distinct
        # unless combined with many-to-many joins that cause duplication.

    # Apply distinct if needed (re-evaluate if using .any() fixed duplication issues)
    # if needs_distinct:
    #    query = query.distinct() # May not be needed with .any() filtering

    # --- Sorting ---
    sort_by = request.args.get('sort_by', 'title', type=str).lower()
    order = request.args.get('order', 'asc', type=str).lower()

    sort_column = getattr(Book, sort_by, None)
    # Allow sorting by seller name or location requires join and alias potentially
    if sort_column is None or sort_by in ['authors', 'categories']: # Prevent sorting on relationship lists
        sort_column = Book.title
        sort_by = 'title'

    if order == 'desc':
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    # --- Pagination ---
    try:
        paginated_books = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        return jsonify({
            "books": [serialize_book_list_item(book) for book in paginated_books.items],
            "total": paginated_books.total,
            "page": paginated_books.page,
            "per_page": paginated_books.per_page,
            "pages": paginated_books.pages,
            "has_prev": paginated_books.has_prev,
            "has_next": paginated_books.has_next,
            "prev_num": paginated_books.prev_num if paginated_books.has_prev else None,
            "next_num": paginated_books.next_num if paginated_books.has_next else None,
            "applied_filters": request.args
        }), 200
    except Exception as e:
        print(f"Error during book listing: {e}")
        abort(500, description="An error occurred while retrieving books.")


# GET /api/v1/books/{book_id} (Guest, User, Seller, Admin)
@book_bp.route('/<int:book_id>', methods=['GET'])
def get_book_details(book_id):
    """
    Get details of a specific book. Public detail view.
    """
    # Eager load relationships needed for the detail view
    book = Book.query.options(
        joinedload(Book.authors),
        joinedload(Book.categories),
        joinedload(Book.publisher),
        joinedload(Book.seller),
        # joinedload(Book.ratings).joinedload(Rating.user) # Example deeper load if needed
    ).get_or_404(book_id, description=f"Book with ID {book_id} not found.")

    return jsonify(serialize_book_detail(book)), 200


# GET /api/v1/books/sellers/me (Seller)
@book_bp.route('/sellers/me', methods=['GET'])
@login_required
@role_seller
def list_current_seller_books():
    """
    List books listed by the current seller (paginated).
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    seller = Seller.query.filter_by(user_id=g.user.id).first_or_404(
        description="Seller profile not found for the current user."
    )

    try:
        # Eager load relationships for serialization
        query = Book.query.options(
            joinedload(Book.authors),
            joinedload(Book.categories),
            joinedload(Book.publisher)
        ).filter_by(seller_id=seller.id).order_by(Book.title)

        paginated_books = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            "books": [serialize_book_list_item(book) for book in paginated_books.items],
            "total": paginated_books.total,
            "page": paginated_books.page,
            "per_page": paginated_books.per_page,
            "pages": paginated_books.pages
            # Add other pagination fields if needed
        }), 200
    except Exception as e:
        print(f"Error listing current seller books: {e}")
        abort(500, description="An error occurred while retrieving seller's books.")


# GET /api/v1/books/sellers/{seller_id} (Guest, User, Seller, Admin)
@book_bp.route('/sellers/<int:seller_id>', methods=['GET'])
def list_seller_books(seller_id):
    """
    List books listed by a specific seller (paginated).
    """
    # Check if seller exists first
    seller = Seller.query.get_or_404(seller_id, description=f"Seller with ID {seller_id} not found.")

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    try:
         # Eager load relationships for serialization
        query = Book.query.options(
            joinedload(Book.authors),
            joinedload(Book.categories),
            joinedload(Book.publisher)
        ).filter_by(seller_id=seller.id).order_by(Book.title)

        paginated_books = query.paginate(page=page, per_page=per_page, error_out=False)

        return jsonify({
            "books": [serialize_book_list_item(book) for book in paginated_books.items],
            "total": paginated_books.total,
            "page": paginated_books.page,
            "per_page": paginated_books.per_page,
            "pages": paginated_books.pages
            # Add other pagination fields if needed
        }), 200
    except Exception as e:
        print(f"Error listing seller {seller_id} books: {e}")
        abort(500, description="An error occurred while retrieving seller's books.")


# PATCH /api/v1/books/{book_id} (Seller, Admin)
@book_bp.route('/<int:book_id>', methods=['PATCH'])
@login_required
@roles_required('Seller', 'Admin')
def update_book_details(book_id):
    """
    Update a book's details.
    Sellers can only update their own books. Admins can update any.
    Allows updating: title, description, price, quantity, discount_percent,
                     image_urls, publisher_id, author_ids, category_ids.
    """
    book = Book.query.options(
        joinedload(Book.seller) # Load seller for ownership check
        ).get_or_404(book_id, description=f"Book with ID {book_id} not found.")

    # --- Authorization Check ---
    if g.user.role == 'Seller':
        # Ensure the seller profile exists and matches the book's seller
        seller = Seller.query.filter_by(user_id=g.user.id).first()
        if not seller or book.seller_id != seller.id:
            abort(403, description="Sellers can only update their own book listings.")
    # Admin role already checked by decorator

    data = request.get_json()
    if not data:
        abort(400, description="No update data provided.")

    updated = False # Flag to track if any changes were made

    # --- Update Fields ---
    if 'title' in data:
        book.title = data['title']
        updated = True
    if 'description' in data:
        book.description = data['description']
        updated = True
    if 'price' in data:
        try:
            price = Decimal(data['price'])
            if price <= 0: raise ValueError()
            book.price = price
            updated = True
        except (ValueError, TypeError, InvalidOperation):
             abort(400, description="Invalid format for price.")
    if 'quantity' in data:
        try:
            quantity = int(data['quantity'])
            if quantity < 0: raise ValueError()
            book.quantity = quantity
            updated = True
        except (ValueError, TypeError):
             abort(400, description="Invalid format for quantity.")
    if 'discount_percent' in data:
         try:
            discount = int(data['discount_percent'])
            if not (0 <= discount <= 100): raise ValueError()
            book.discount_percent = discount
            updated = True
         except (ValueError, TypeError):
             abort(400, description="Invalid format for discount_percent (must be 0-100).")
    # Update image URLs if provided
    for i in range(1, 4):
        key = f'image_url_{i}'
        if key in data:
            setattr(book, key, data[key])
            updated = True

    # --- Update Relationships ---
    if 'publisher_id' in data:
        pub_id = data['publisher_id']
        if pub_id is None:
            book.publisher = None # Allow unsetting publisher
            updated = True
        else:
            try:
                publisher = Publisher.query.get(int(pub_id))
                if not publisher:
                     abort(404, description=f"Publisher with ID {pub_id} not found.")
                book.publisher = publisher
                updated = True
            except (ValueError, TypeError):
                abort(400, description="Invalid format for publisher_id.")

    if 'author_ids' in data:
        try:
            author_ids = [int(aid) for aid in data['author_ids']]
            authors = Author.query.filter(Author.id.in_(author_ids)).all()
            if len(authors) != len(author_ids):
                 abort(404, description="One or more specified authors not found for update.")
            book.authors = authors # Replace existing authors
            updated = True
        except (ValueError, TypeError):
             abort(400, description="Invalid format for author_ids list.")

    if 'category_ids' in data:
        try:
            category_ids = [int(cid) for cid in data['category_ids']]
            categories = Category.query.filter(Category.id.in_(category_ids)).all()
            if len(categories) != len(category_ids):
                 abort(404, description="One or more specified categories not found for update.")
            book.categories = categories # Replace existing categories
            updated = True
        except (ValueError, TypeError):
             abort(400, description="Invalid format for category_ids list.")


    if not updated:
        return jsonify({"message": "No changes detected."}), 200 # Or 304 Not Modified

    try:
        db.session.commit()
        # Reload the book with relationships for the response
        book_updated = Book.query.options(
            joinedload(Book.authors), joinedload(Book.categories),
            joinedload(Book.publisher), joinedload(Book.seller)
        ).get(book_id)
        return jsonify(serialize_book_detail(book_updated)), 200
    except IntegrityError as e:
        db.session.rollback()
        print(f"Integrity Error on book update: {e}")
        abort(500, description="Database error occurred while updating the book.")
    except Exception as e:
        db.session.rollback()
        print(f"Unexpected Error on book update: {e}")
        abort(500, description="An unexpected error occurred during update.")


# DELETE /api/v1/books/{book_id} (Seller, Admin)
@book_bp.route('/<int:book_id>', methods=['DELETE'])
@login_required
@roles_required('Seller', 'Admin')
def remove_book_listing(book_id):
    """
    Remove a book listing.
    Sellers can only delete their own books. Admins can delete any.
    """
    book = Book.query.options(
        joinedload(Book.seller) # Load seller for ownership check
        ).get_or_404(book_id, description=f"Book with ID {book_id} not found.")

    # --- Authorization Check ---
    if g.user.role == 'Seller':
        seller = Seller.query.filter_by(user_id=g.user.id).first()
        if not seller or book.seller_id != seller.id:
            abort(403, description="Sellers can only delete their own book listings.")
    # Admin role already checked by decorator

    try:
        # Relationships (like ratings) might cascade delete if configured in the model
        db.session.delete(book)
        db.session.commit()
        return jsonify({"message": f"Book ID {book_id} deleted successfully."}), 200
        # Standard practice is to return 204 No Content on successful DELETE
        # return '', 204
    except Exception as e:
        db.session.rollback()
        print(f"Error deleting book {book_id}: {e}")
        abort(500, description="An error occurred while deleting the book.")

