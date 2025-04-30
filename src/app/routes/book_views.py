# src/app/views/book_views.py

import logging
from decimal import Decimal, InvalidOperation
from flask import Blueprint, request, jsonify, g, abort
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload, selectinload # For efficient loading

# Import database session and models
from ..extensions import db
from ..model.book import Book
from ..model.seller import Seller
from ..model.author import Author
from ..model.category import Category
from ..model.publisher import Publisher
# Assuming User model might be needed indirectly via g.user
# from ..model.user import User

# Configure basic logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

def login_required(f): return f
def role_admin(f): return f
def role_seller(f): return f
def roles_required(f): return f

# --- Helper Function for Seller ID ---
def get_current_seller_id():
    """Gets the seller ID for the currently logged-in user."""
    if not hasattr(g, 'user') or not g.user:
        log.error("Attempted to get seller ID without logged-in user.")
        abort(401, "Authentication required to perform this action.") # Should be caught by @login_required usually

    if g.user.role != 'Seller' and g.user.role != 'Admin':
         # This check might be redundant if @roles_required is used, but good for clarity
         log.warning(f"User {g.user.id} with role {g.user.role} attempted seller action.")
         abort(403, "User is not a Seller.")

    # Find the seller profile linked to the user
    seller = Seller.query.filter_by(user_id=g.user.id).first()
    if not seller and g.user.role == 'Seller':
        # This indicates an inconsistency: User has Seller role but no Seller profile
        log.error(f"Data inconsistency: User {g.user.id} has role 'Seller' but no associated Seller profile.")
        abort(404, description="Seller profile not found for the current user.")
    # Admins might not have a seller profile, they operate on behalf of others or system-wide
    return seller.id if seller else None


# --- Helper Functions for Serialization ---
def serialize_author_simple(author):
    """Simple serialization for author linked to a book."""
    if not author:
        return None
    return {
        'id': author.id,
        'first_name': author.first_name,
        'last_name': author.last_name,
    }

def serialize_category_simple(category):
    """Simple serialization for category linked to a book."""
    if not category:
        return None
    return {
        'id': category.id,
        'name': category.name,
    }

def serialize_publisher_simple(publisher):
    """Simple serialization for publisher linked to a book."""
    if not publisher:
        return None
    return {
        'id': publisher.id,
        'name': publisher.name,
    }

def serialize_seller_simple(seller):
    """Simple serialization for seller linked to a book."""
    if not seller:
        return None
    return {
        'id': seller.id,
        'name': seller.name,
        'user_id': seller.user_id
    }

def serialize_book(book, detail_level='list'):
    """
    Converts a Book object into a dictionary.
    detail_level: 'list' (basic info), 'detail' (includes more fields like description, all images)
    """
    if not book:
        return None

    data = {
        'id': book.id,
        'title': book.title,
        'price': str(book.price) if book.price is not None else None, # Convert Decimal to string
        'quantity': book.quantity,
        'discount_percent': book.discount_percent,
        'average_rating': str(book.rating) if book.rating is not None else None, # Assuming 'rating' holds avg
        'image_url_1': book.image_url_1,
        # --- Relationships ---
        'author': serialize_author_simple(book.author),
        'categories': [serialize_category_simple(cat) for cat in book.categories],
        'publisher': serialize_publisher_simple(book.publisher),
        'seller': serialize_seller_simple(book.seller),
        # --- Timestamps ---
        'created_at': book.created_at.isoformat() if book.created_at else None,
        'updated_at': book.updated_at.isoformat() if book.updated_at else None,
    }

    if detail_level == 'detail':
        data.update({
            'description': book.description,
            'image_url_2': book.image_url_2,
            'image_url_3': book.image_url_3,
            # Potentially add more details like list of ratings if needed
        })

    return data


# --- Create Blueprint ---
book_bp = Blueprint('book_bp', __name__, url_prefix='/api/v1/books')


# --- Book Model Endpoints ---

# POST /api/v1/books/ (Seller, Admin)
@book_bp.route('/', methods=['POST'])
@login_required
@roles_required('Seller', 'Admin')
def add_book_listing():
    """
    Add a new book listing.
    Accessible by: Seller, Admin
    `seller_id` linked to current user if Seller, or specified if Admin.
    Requires author_id, category_ids (list). publisher_id is optional.
    """
    data = request.get_json()
    if not data:
        abort(400, description="Invalid request: No JSON data provided.")

    # --- Validation ---
    required_fields = ['title', 'price', 'quantity', 'author_id', 'category_ids']
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    if missing_fields:
        abort(400, description=f"Missing required fields: {', '.join(missing_fields)}")

    # Validate data types and values
    try:
        title = str(data['title']).strip()
        price = Decimal(data['price'])
        quantity = int(data['quantity'])
        author_id = int(data['author_id'])
        category_ids = [int(cid) for cid in data['category_ids']] # Expecting a list of IDs
        discount_percent = int(data.get('discount_percent', 0))
        publisher_id = int(data['publisher_id']) if data.get('publisher_id') is not None else None
        description = data.get('description')
        image_url_1 = data.get('image_url_1')
        image_url_2 = data.get('image_url_2')
        image_url_3 = data.get('image_url_3')

        if not title:
             abort(400, description="Title cannot be empty.")
        if price <= 0:
            abort(400, description="Price must be positive.")
        if quantity < 0:
            abort(400, description="Quantity cannot be negative.")
        if not 0 <= discount_percent <= 100:
            abort(400, description="Discount percent must be between 0 and 100.")
        if not category_ids:
             abort(400, description="At least one category ID must be provided.")

    except (ValueError, TypeError, InvalidOperation) as e:
        log.warning(f"Data validation failed during book creation: {e}", exc_info=True)
        abort(400, description=f"Invalid data format or value: {e}")

    # --- Determine Seller ID ---
    seller_id = None
    if g.user.role == 'Admin':
        # Admin can specify seller_id, otherwise it might be null or linked to a default admin seller?
        # For now, require Admin to specify if not linking to themselves (if they have a profile)
        specified_seller_id = data.get('seller_id')
        if specified_seller_id:
            seller = Seller.query.get(int(specified_seller_id))
            if not seller:
                abort(404, description=f"Seller with ID {specified_seller_id} not found.")
            seller_id = seller.id
        else:
            # If Admin doesn't specify, maybe default to their own profile if they have one?
            # Or abort? Let's abort for now to be explicit.
             admin_seller_id = get_current_seller_id() # Check if admin has a seller profile
             if admin_seller_id:
                 seller_id = admin_seller_id
                 log.info(f"Admin {g.user.id} creating book under their own seller profile {seller_id}.")
             else:
                 abort(400, description="Admin must specify a valid 'seller_id' as they don't have a seller profile.")

    elif g.user.role == 'Seller':
        seller_id = get_current_seller_id() # Gets the seller ID linked to the logged-in user
        if not seller_id:
             # Should have been caught by get_current_seller_id, but double-check
             abort(404, description="Could not find seller profile for the current user.")
        # Ensure seller doesn't try to specify a different seller_id
        if 'seller_id' in data and data['seller_id'] != seller_id:
            log.warning(f"Seller {g.user.id} attempted to list book under different seller ID {data['seller_id']}.")
            abort(403, description="Sellers can only list books under their own profile.")

    if not seller_id:
         # Should not happen if logic above is correct
         log.error("Failed to determine seller_id.")
         abort(500, description="Internal error: Could not determine seller for the book.")


    # --- Fetch Related Objects ---
    author = Author.query.get(author_id)
    if not author:
        abort(404, description=f"Author with ID {author_id} not found.")

    categories = Category.query.filter(Category.id.in_(category_ids)).all()
    if len(categories) != len(category_ids):
        found_ids = {cat.id for cat in categories}
        missing_ids = [cid for cid in category_ids if cid not in found_ids]
        abort(404, description=f"Category IDs not found: {', '.join(map(str, missing_ids))}")

    publisher = None
    if publisher_id:
        publisher = Publisher.query.get(publisher_id)
        if not publisher:
            abort(404, description=f"Publisher with ID {publisher_id} not found.")

    # --- Create Book ---
    new_book = Book(
        title=title,
        price=price,
        quantity=quantity,
        discount_percent=discount_percent,
        description=description,
        image_url_1=image_url_1,
        image_url_2=image_url_2,
        image_url_3=image_url_3,
        # --- Link Relationships ---
        author_id=author.id,
        publisher_id=publisher.id if publisher else None,
        seller_id=seller_id
    )
    # Add categories (many-to-many)
    new_book.categories.extend(categories)

    # --- Database Operation ---
    try:
        db.session.add(new_book)
        db.session.commit()
        log.info(f"Book '{title}' (ID: {new_book.id}) created successfully by user {g.user.id} (Role: {g.user.role}) for seller {seller_id}.")
        # Serialize with detail level 'detail' for the response
        return jsonify(serialize_book(new_book, detail_level='detail')), 201
    except IntegrityError as e:
        db.session.rollback()
        log.error(f"Database integrity error while adding book '{title}': {e}", exc_info=True)
        abort(500, description=f"Database error occurred while adding book. Possible constraint violation: {e}")
    except Exception as e:
        db.session.rollback()
        log.error(f"Unexpected error while adding book '{title}': {e}", exc_info=True)
        abort(500, description="An unexpected error occurred while adding the book.")


# GET /api/v1/books/ (Guest, User, Seller, Admin)
@book_bp.route('/', methods=['GET'])
def list_books():
    """
    List all books (paginated, filterable, searchable). Public listing.
    Accessible by: Guest, User, Seller, Admin
    Filters: category_id, author_id, publisher_id, seller_id, min_price, max_price, min_rating, search (title/desc).
    Sorting: sort_by (e.g., price, rating, created_at), sort_order (asc, desc).
    """
    # --- Pagination ---
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        if page < 1 or per_page < 1 or per_page > 100: # Add limits
             abort(400, description="Invalid pagination parameters. page >= 1, 1 <= per_page <= 100.")
    except ValueError:
         abort(400, description="Invalid pagination parameters. page and per_page must be integers.")

    # --- Base Query ---
    # Eager load relationships commonly needed for list view to avoid N+1 queries
    query = Book.query.options(
        selectinload(Book.author),
        selectinload(Book.categories),
        selectinload(Book.publisher),
        selectinload(Book.seller)
    )

    # --- Filtering ---
    try:
        if 'author_id' in request.args:
            query = query.filter(Book.author_id == int(request.args['author_id']))
        if 'publisher_id' in request.args:
            query = query.filter(Book.publisher_id == int(request.args['publisher_id']))
        if 'seller_id' in request.args:
            query = query.filter(Book.seller_id == int(request.args['seller_id']))
        if 'category_id' in request.args:
            # For many-to-many, check if the book's categories contain the given category_id
            query = query.filter(Book.categories.any(Category.id == int(request.args['category_id'])))
        if 'min_price' in request.args:
            query = query.filter(Book.price >= Decimal(request.args['min_price']))
        if 'max_price' in request.args:
            query = query.filter(Book.price <= Decimal(request.args['max_price']))
        if 'min_rating' in request.args:
            # Assuming 'rating' column holds the average rating
            query = query.filter(Book.rating >= Decimal(request.args['min_rating']))
    except (ValueError, InvalidOperation) as e:
        abort(400, description=f"Invalid filter value: {e}")

    # --- Searching ---
    if 'search' in request.args:
        search_term = f"%{request.args['search']}%"
        # Search in title and description (case-insensitive)
        query = query.filter(
            db.or_(
                Book.title.ilike(search_term),
                Book.description.ilike(search_term)
                # Could potentially add author name search here with a join
                # Author.first_name.ilike(search_term),
                # Author.last_name.ilike(search_term)
            )
        )
        # Example join for author search (if needed):
        # query = query.join(Author).filter(
        #     db.or_(
        #         Book.title.ilike(search_term),
        #         Book.description.ilike(search_term),
        #         Author.first_name.ilike(search_term),
        #         Author.last_name.ilike(search_term)
        #     )
        # )


    # --- Sorting ---
    sort_by = request.args.get('sort_by', 'created_at') # Default sort
    sort_order = request.args.get('sort_order', 'desc').lower()

    sort_column = getattr(Book, sort_by, None)
    if sort_column is None:
        # Prevent sorting by arbitrary/invalid columns
        sort_column = Book.created_at # Default back
        sort_order = 'desc'

    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc()) # Default to desc

    # --- Execute Query ---
    try:
        paginated_books = query.paginate(page=page, per_page=per_page, error_out=False)
        books_data = [serialize_book(book, detail_level='list') for book in paginated_books.items]

        return jsonify({
            'books': books_data,
            'total': paginated_books.total,
            'pages': paginated_books.pages,
            'current_page': paginated_books.page,
            'per_page': paginated_books.per_page,
            'has_next': paginated_books.has_next,
            'has_prev': paginated_books.has_prev,
            # Include applied filters/sort for context? Optional.
            'filters': request.args.to_dict()
        }), 200
    except Exception as e:
        log.error(f"Error retrieving book list: {e}", exc_info=True)
        abort(500, description="An error occurred while retrieving books.")


# GET /api/v1/books/{book_id} (Guest, User, Seller, Admin)
@book_bp.route('/<int:book_id>', methods=['GET'])
def get_book_details(book_id):
    """
    Get details of a specific book. Public detail view.
    Accessible by: Guest, User, Seller, Admin
    """
    try:
        # Eager load relationships needed for detailed view
        book = Book.query.options(
            joinedload(Book.author),
            selectinload(Book.categories), # Use selectinload for many-to-many
            joinedload(Book.publisher),
            joinedload(Book.seller)
            # Could also load ratings here if needed: selectinload(Book.ratings).joinedload(Rating.user)
        ).get_or_404(book_id, description=f"Book with ID {book_id} not found.")

        # Serialize with 'detail' level
        return jsonify(serialize_book(book, detail_level='detail')), 200
    except Exception as e:
         # Catch potential errors during serialization or other issues
        log.error(f"Error retrieving details for book {book_id}: {e}", exc_info=True)
        # get_or_404 handles not found, so this is likely a 500 unless serialization fails specifically
        abort(500, description=f"An error occurred while retrieving details for book {book_id}.")


# GET /api/v1/books/sellers/me (Seller)
@book_bp.route('/sellers/me', methods=['GET'])
@login_required
@roles_required('Seller') # Only Sellers can access this
def list_current_seller_books():
    """
    List books listed by the currently logged-in seller (paginated).
    Accessible by: Seller
    """
    seller_id = get_current_seller_id()
    if not seller_id:
        # This case should ideally be handled by get_current_seller_id aborting,
        # but as a safeguard:
        abort(404, description="Seller profile not found for the current user.")

    # --- Use the generic list_books logic but force the seller_id filter ---
    # This avoids duplicating pagination, filtering, sorting logic.
    # We modify the request args *before* passing them to a potential shared function,
    # or we implement the query directly here. Let's implement directly for clarity.

    # --- Pagination ---
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        if page < 1 or per_page < 1 or per_page > 100:
             abort(400, description="Invalid pagination parameters.")
    except ValueError:
         abort(400, description="Invalid pagination parameters.")

    # --- Base Query (filtered by current seller) ---
    query = Book.query.filter(Book.seller_id == seller_id).options(
        selectinload(Book.author),
        selectinload(Book.categories),
        selectinload(Book.publisher),
        selectinload(Book.seller) # Seller will always be the same here, but keep for serializer
    )

    # --- Apply Optional Filters (e.g., search within own books) ---
    if 'search' in request.args:
        search_term = f"%{request.args['search']}%"
        query = query.filter(
            db.or_(
                Book.title.ilike(search_term),
                Book.description.ilike(search_term)
            )
        )
    # Add other filters if needed (e.g., filter own books by category)
    if 'category_id' in request.args:
        try:
            query = query.filter(Book.categories.any(Category.id == int(request.args['category_id'])))
        except ValueError:
             abort(400, description="Invalid category_id filter.")

    # --- Sorting ---
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc').lower()
    sort_column = getattr(Book, sort_by, Book.created_at)
    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # --- Execute Query ---
    try:
        paginated_books = query.paginate(page=page, per_page=per_page, error_out=False)
        books_data = [serialize_book(book, detail_level='list') for book in paginated_books.items]

        return jsonify({
            'books': books_data,
            'seller_id': seller_id, # Context
            'total': paginated_books.total,
            'pages': paginated_books.pages,
            'current_page': paginated_books.page,
            'per_page': paginated_books.per_page,
            'has_next': paginated_books.has_next,
            'has_prev': paginated_books.has_prev
        }), 200
    except Exception as e:
        log.error(f"Error retrieving books for current seller (ID: {seller_id}): {e}", exc_info=True)
        abort(500, description="An error occurred while retrieving your books.")


# GET /api/v1/books/sellers/{seller_id} (Guest, User, Seller, Admin)
@book_bp.route('/sellers/<int:seller_id>', methods=['GET'])
def list_seller_books(seller_id):
    """
    List books listed by a specific seller (paginated).
    Accessible by: Guest, User, Seller, Admin
    """
    # --- Check if Seller Exists ---
    seller = Seller.query.get_or_404(seller_id, description=f"Seller with ID {seller_id} not found.")

    # --- Pagination ---
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        if page < 1 or per_page < 1 or per_page > 100:
             abort(400, description="Invalid pagination parameters.")
    except ValueError:
         abort(400, description="Invalid pagination parameters.")

    # --- Base Query (filtered by specified seller) ---
    query = Book.query.filter(Book.seller_id == seller_id).options(
        selectinload(Book.author),
        selectinload(Book.categories),
        selectinload(Book.publisher),
        # No need to load seller again, we already have it via get_or_404
        # but serializer expects it, so keep it consistent maybe?
        # Or adjust serializer. Let's load it for consistency for now.
        selectinload(Book.seller)
    )

    # --- Apply Optional Filters (e.g., search within this seller's books) ---
    if 'search' in request.args:
        search_term = f"%{request.args['search']}%"
        query = query.filter(
            db.or_(
                Book.title.ilike(search_term),
                Book.description.ilike(search_term)
            )
        )
    if 'category_id' in request.args:
        try:
            query = query.filter(Book.categories.any(Category.id == int(request.args['category_id'])))
        except ValueError:
             abort(400, description="Invalid category_id filter.")

    # --- Sorting ---
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc').lower()
    sort_column = getattr(Book, sort_by, Book.created_at)
    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # --- Execute Query ---
    try:
        paginated_books = query.paginate(page=page, per_page=per_page, error_out=False)
        books_data = [serialize_book(book, detail_level='list') for book in paginated_books.items]

        return jsonify({
            'books': books_data,
            'seller_info': serialize_seller_simple(seller), # Include seller info
            'total': paginated_books.total,
            'pages': paginated_books.pages,
            'current_page': paginated_books.page,
            'per_page': paginated_books.per_page,
            'has_next': paginated_books.has_next,
            'has_prev': paginated_books.has_prev
        }), 200
    except Exception as e:
        log.error(f"Error retrieving books for seller {seller_id}: {e}", exc_info=True)
        abort(500, description=f"An error occurred while retrieving books for seller {seller_id}.")


# PATCH /api/v1/books/{book_id} (Seller, Admin)
@book_bp.route('/<int:book_id>', methods=['PATCH'])
@login_required
@roles_required('Seller', 'Admin')
def update_book_details(book_id):
    """
    Update a book's details.
    Accessible by: Seller (only their own books), Admin (any book).
    Allows updating fields like title, description, price, quantity, discount, images,
    and potentially relationships (author, categories, publisher).
    """
    # --- Get Book and Check Ownership/Permissions ---
    book = Book.query.options(
        selectinload(Book.categories) # Load categories for potential update
    ).get_or_404(book_id, description=f"Book with ID {book_id} not found.")

    if g.user.role == 'Seller':
        current_seller_id = get_current_seller_id()
        if not current_seller_id or book.seller_id != current_seller_id:
            log.warning(f"Seller {g.user.id} (Seller Profile: {current_seller_id}) attempted to update book {book_id} owned by seller {book.seller_id}.")
            abort(403, description="Forbidden: You can only update your own book listings.")
    # Admin has permission implicitly via roles_required decorator

    # --- Get Update Data ---
    data = request.get_json()
    if not data:
        abort(400, description="Invalid request: No JSON data provided for update.")

    updated_fields = []

    # --- Update Fields ---
    try:
        if 'title' in data:
            title = str(data['title']).strip()
            if not title: abort(400, "Title cannot be empty.")
            if title != book.title:
                book.title = title
                updated_fields.append('title')
        if 'description' in data:
            description = data['description'] # Allow null/empty
            if description != book.description:
                book.description = description
                updated_fields.append('description')
        if 'price' in data:
            price = Decimal(data['price'])
            if price <= 0: abort(400, "Price must be positive.")
            if price != book.price:
                book.price = price
                updated_fields.append('price')
        if 'quantity' in data:
            quantity = int(data['quantity'])
            if quantity < 0: abort(400, "Quantity cannot be negative.")
            if quantity != book.quantity:
                book.quantity = quantity
                updated_fields.append('quantity')
        if 'discount_percent' in data:
            discount = int(data['discount_percent'])
            if not 0 <= discount <= 100: abort(400, "Discount percent must be between 0 and 100.")
            if discount != book.discount_percent:
                book.discount_percent = discount
                updated_fields.append('discount_percent')
        # Update image URLs if provided
        for i in range(1, 4):
            key = f'image_url_{i}'
            if key in data:
                 url = data[key] # Allow null/empty string to clear URL
                 if url != getattr(book, key):
                     setattr(book, key, url)
                     updated_fields.append(key)

        # --- Update Relationships (Optional - More Complex) ---
        if 'author_id' in data:
            new_author_id = int(data['author_id'])
            if new_author_id != book.author_id:
                new_author = Author.query.get(new_author_id)
                if not new_author: abort(404, f"Author with ID {new_author_id} not found.")
                book.author_id = new_author_id
                # Eager load the new author for the response serialization
                book.author = new_author
                updated_fields.append('author_id')

        if 'publisher_id' in data:
             # Allow setting publisher to null
            new_publisher_id = int(data['publisher_id']) if data['publisher_id'] is not None else None
            if new_publisher_id != book.publisher_id:
                new_publisher = None
                if new_publisher_id is not None:
                    new_publisher = Publisher.query.get(new_publisher_id)
                    if not new_publisher: abort(404, f"Publisher with ID {new_publisher_id} not found.")
                book.publisher_id = new_publisher_id
                book.publisher = new_publisher # Update relationship proxy
                updated_fields.append('publisher_id')

        if 'category_ids' in data:
            new_category_ids = set(int(cid) for cid in data['category_ids']) # Use a set for efficiency
            current_category_ids = {cat.id for cat in book.categories}

            if new_category_ids != current_category_ids:
                # Find categories to add and remove
                ids_to_add = new_category_ids - current_category_ids
                ids_to_remove = current_category_ids - new_category_ids

                # Remove old categories
                if ids_to_remove:
                    cats_to_remove = [cat for cat in book.categories if cat.id in ids_to_remove]
                    for cat in cats_to_remove:
                        book.categories.remove(cat)

                # Add new categories
                if ids_to_add:
                    new_categories = Category.query.filter(Category.id.in_(ids_to_add)).all()
                    if len(new_categories) != len(ids_to_add):
                         found_ids = {cat.id for cat in new_categories}
                         missing = ids_to_add - found_ids
                         abort(404, f"Category IDs not found for update: {', '.join(map(str, missing))}")
                    book.categories.extend(new_categories)

                updated_fields.append('categories')

    except (ValueError, TypeError, InvalidOperation) as e:
        log.warning(f"Data validation failed during book update (ID: {book_id}): {e}", exc_info=True)
        abort(400, description=f"Invalid data format or value for update: {e}")
    except abort.HTTPException: # Re-raise aborts from validation
        raise
    except Exception as e: # Catch unexpected errors during validation/lookup
        log.error(f"Unexpected error during validation/lookup for book update (ID: {book_id}): {e}", exc_info=True)
        abort(500, "An unexpected error occurred during the update process.")


    if not updated_fields:
         # Return 304 Not Modified? Or just the current data? Let's return current data.
         log.info(f"No fields updated for book {book_id}.")
         # Need to reload relationships if they weren't loaded initially or might have changed
         # Re-querying or using session.refresh might be options.
         # For simplicity, let's re-serialize the potentially modified object.
         # Make sure relationships needed by serializer are loaded/refreshed if necessary.
         # Re-fetch with loads might be safest if relationships were modified.
         book_refreshed = Book.query.options(
             joinedload(Book.author),
             selectinload(Book.categories),
             joinedload(Book.publisher),
             joinedload(Book.seller)
         ).get(book_id)
         return jsonify(serialize_book(book_refreshed, detail_level='detail')), 200


    # --- Database Commit ---
    try:
        db.session.commit()
        log.info(f"Book {book_id} updated successfully by user {g.user.id}. Fields changed: {', '.join(updated_fields)}")
        # Re-fetch or use the committed object for the response.
        # The 'book' object in memory should reflect the committed state.
        # Ensure relationships are loaded for serialization if they were changed.
        # The options loaded initially might suffice if only simple fields changed.
        # If relationships changed, the object's relationship attributes should be updated.
        return jsonify(serialize_book(book, detail_level='detail')), 200
    except IntegrityError as e:
        db.session.rollback()
        log.error(f"Database integrity error while updating book {book_id}: {e}", exc_info=True)
        abort(500, description=f"Database error occurred during update. Constraint violation: {e}")
    except Exception as e:
        db.session.rollback()
        log.error(f"Unexpected error while committing book update {book_id}: {e}", exc_info=True)
        abort(500, description="An unexpected error occurred during update.")


# DELETE /api/v1/books/{book_id} (Seller, Admin)
@book_bp.route('/<int:book_id>', methods=['DELETE'])
@login_required
@roles_required('Seller', 'Admin')
def remove_book_listing(book_id):
    """
    Remove a book listing.
    Accessible by: Seller (only their own books), Admin (any book).
    """
    # --- Get Book and Check Ownership/Permissions ---
    book = Book.query.get_or_404(book_id, description=f"Book with ID {book_id} not found.")
    book_title = book.title # For logging

    if g.user.role == 'Seller':
        current_seller_id = get_current_seller_id()
        if not current_seller_id or book.seller_id != current_seller_id:
            log.warning(f"Seller {g.user.id} (Seller Profile: {current_seller_id}) attempted to DELETE book {book_id} owned by seller {book.seller_id}.")
            abort(403, description="Forbidden: You can only delete your own book listings.")
    # Admin has permission

    # --- Database Deletion ---
    try:
        # Deletion might cascade based on relationship settings (e.g., ratings)
        db.session.delete(book)
        db.session.commit()
        log.info(f"Book {book_id} ('{book_title}') deleted successfully by user {g.user.id} (Role: {g.user.role}).")
        # Standard practice is to return 204 No Content on successful DELETE
        return '', 204
    except Exception as e:
        db.session.rollback()
        log.error(f"Error deleting book {book_id} ('{book_title}'): {e}", exc_info=True)
        abort(500, description=f"An error occurred while deleting book {book_id}.")
