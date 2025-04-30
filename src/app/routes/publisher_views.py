from flask import Blueprint, request, jsonify, g, abort
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from ..extensions import db
from ..model.publisher import Publisher
from ..model.book import Book

def login_required(f):return f
def role_admin(f):return f
def role_seller(f): return f

def roles_required(*roles):
    def wrapper(f):
                return f
    return wrapper

# --- Helper Function for Serialization (Simple Example) ---
def serialize_publisher(publisher):
    """Converts a Publisher object to a dictionary."""
    if not publisher:
        return None
    return {
        'id': publisher.id,
        'name': publisher.name,
        'created_at': publisher.created_at.isoformat() if publisher.created_at else None,
        'updated_at': publisher.updated_at.isoformat() if publisher.updated_at else None
    }

def serialize_book_simple(book):
    """Converts a Book object to a simple dictionary (for list views)."""
    if not book:
        return None
    return {
        'id': book.id,
        'title': book.title,
        'price': float(book.price) if book.price is not None else None, # Ensure price is float for JSON
        'author_id': book.author_id, # Assuming author_id is sufficient here
        'publisher_id': book.publisher_id
    }

# --- Create Blueprint ---
publisher_bp = Blueprint('publisher_bp', __name__, url_prefix='/api/v1/publishers')

# --- Publisher Model Endpoints ---

# POST /api/v1/publishers/ (Admin, Seller)
@publisher_bp.route('/', methods=['POST'])
@login_required
@roles_required('Admin', 'Seller')
def add_publisher():
    """
    Add a new publisher.
    Accessible by: Admin, Seller
    Request Body: {"name": "Publisher Name"}
    """
    data = request.get_json()
    if not data or 'name' not in data or not data['name'].strip():
        abort(400, description="Publisher name is required.")

    name = data['name'].strip()

    # Check if publisher already exists
    existing_publisher = Publisher.query.filter(Publisher.name.ilike(name)).first()
    if existing_publisher:
        # Using 409 Conflict as the resource (publisher with this name) already exists
        abort(409, description=f"Publisher with name '{name}' already exists.")

    new_publisher = Publisher(name=name)

    try:
        db.session.add(new_publisher)
        db.session.commit()
        return jsonify(serialize_publisher(new_publisher)), 201
    except IntegrityError as e: # Catch potential race conditions or other DB constraints
        db.session.rollback()
        # Log the error e
        abort(409, description=f"Could not add publisher. Name might already exist. Error: {e}")
    except SQLAlchemyError as e:
        db.session.rollback()
        # Log the error e
        abort(500, description=f"Database error occurred: {e}")


# GET /api/v1/publishers/ (Guest, User, Seller, Admin)
@publisher_bp.route('/', methods=['GET'])
def list_publishers():
    """
    List all publishers (paginated, searchable). Public listing.
    Accessible by: Guest, User, Seller, Admin
    Query Params:
        - page (int, optional): Page number (default: 1)
        - per_page (int, optional): Items per page (default: 10, max: 100)
        - search (str, optional): Search term for publisher name (case-insensitive)
    """
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search_term = request.args.get('search', None, type=str)

        # Clamp per_page to a maximum value
        per_page = min(per_page, 100)
        if page <= 0: page = 1
        if per_page <= 0: per_page = 10


        query = Publisher.query

        if search_term:
            # Use ilike for case-insensitive search
            query = query.filter(Publisher.name.ilike(f'%{search_term}%'))

        query = query.order_by(Publisher.name) # Order alphabetically by name

        paginated_publishers = query.paginate(page=page, per_page=per_page, error_out=False)

        results = [serialize_publisher(p) for p in paginated_publishers.items]

        return jsonify({
            'publishers': results,
            'total_pages': paginated_publishers.pages,
            'current_page': paginated_publishers.page,
            'total_items': paginated_publishers.total,
            'per_page': paginated_publishers.per_page,
            'has_next': paginated_publishers.has_next,
            'has_prev': paginated_publishers.has_prev
        }), 200

    except SQLAlchemyError as e:
        # Log the error e
        abort(500, description=f"Database error occurred while retrieving publishers: {e}")
    except Exception as e:
        # Log the error e
        abort(500, description=f"An unexpected error occurred: {e}")


# GET /api/v1/publishers/{publisher_id} (Guest, User, Seller, Admin)
@publisher_bp.route('/<int:publisher_id>', methods=['GET'])
def get_publisher_details(publisher_id):
    """
    Get details of a specific publisher. Public detail view.
    Accessible by: Guest, User, Seller, Admin
    """
    try:
        publisher = Publisher.query.get_or_404(publisher_id, description=f"Publisher with ID {publisher_id} not found.")
        return jsonify(serialize_publisher(publisher)), 200
    except SQLAlchemyError as e:
        # Log the error e
        abort(500, description=f"Database error occurred: {e}")


# GET /api/v1/publishers/{publisher_id}/books (Guest, User, Seller, Admin)
@publisher_bp.route('/<int:publisher_id>/books', methods=['GET'])
def list_books_by_publisher(publisher_id):
    """
    List books by a specific publisher (paginated).
    Accessible by: Guest, User, Seller, Admin
     Query Params:
        - page (int, optional): Page number (default: 1)
        - per_page (int, optional): Items per page (default: 10, max: 100)
    """
    # First, check if the publisher exists
    publisher = Publisher.query.get_or_404(publisher_id, description=f"Publisher with ID {publisher_id} not found.")

    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)

        # Clamp per_page to a maximum value
        per_page = min(per_page, 100)
        if page <= 0: page = 1
        if per_page <= 0: per_page = 10

        # Query books associated with this publisher
        query = Book.query.filter_by(publisher_id=publisher_id).order_by(Book.title)

        paginated_books = query.paginate(page=page, per_page=per_page, error_out=False)

        results = [serialize_book_simple(b) for b in paginated_books.items]

        return jsonify({
            'books': results,
            'publisher_id': publisher_id,
            'publisher_name': publisher.name, # Include publisher name for context
            'total_pages': paginated_books.pages,
            'current_page': paginated_books.page,
            'total_items': paginated_books.total,
            'per_page': paginated_books.per_page,
            'has_next': paginated_books.has_next,
            'has_prev': paginated_books.has_prev
        }), 200

    except SQLAlchemyError as e:
        # Log the error e
        abort(500, description=f"Database error occurred while retrieving books for publisher {publisher_id}: {e}")
    except Exception as e:
        # Log the error e
        abort(500, description=f"An unexpected error occurred: {e}")


# PATCH /api/v1/publishers/{publisher_id} (Admin)
@publisher_bp.route('/<int:publisher_id>', methods=['PATCH'])
@login_required
@role_admin
def update_publisher_details(publisher_id):
    """
    Update a publisher's details (currently only 'name').
    Accessible by: Admin
    Request Body: {"name": "Updated Publisher Name"} (only fields to update)
    """
    publisher = Publisher.query.get_or_404(publisher_id, description=f"Publisher with ID {publisher_id} not found.")
    data = request.get_json()

    if not data:
        abort(400, description="No update data provided.")

    updated = False
    if 'name' in data:
        new_name = data['name'].strip()
        if not new_name:
            abort(400, description="Publisher name cannot be empty.")
        if new_name != publisher.name:
            # Check if the new name is already taken by *another* publisher
            existing_publisher = Publisher.query.filter(Publisher.name.ilike(new_name), Publisher.id != publisher_id).first()
            if existing_publisher:
                abort(409, description=f"Publisher name '{new_name}' is already in use by another publisher.")
            publisher.name = new_name
            updated = True

    if not updated:
        # Return 304 Not Modified if no changes were made, though often just returning the current state is fine too.
        # Alternatively, return a 200 OK with the unchanged data.
        return jsonify(serialize_publisher(publisher)), 200 # Or return 304 status code

    try:
        db.session.commit()
        return jsonify(serialize_publisher(publisher)), 200
    except IntegrityError as e: # Catch potential race conditions or other DB constraints
        db.session.rollback()
        # Log the error e
        abort(409, description=f"Could not update publisher. Name might already exist. Error: {e}")
    except SQLAlchemyError as e:
        db.session.rollback()
        # Log the error e
        abort(500, description=f"Database error occurred during update: {e}")


# DELETE /api/v1/publishers/{publisher_id} (Admin)
@publisher_bp.route('/<int:publisher_id>', methods=['DELETE'])
@login_required
@role_admin
def delete_publisher(publisher_id):
    """
    Delete a publisher. Prevents deletion if the publisher has associated books.
    Accessible by: Admin
    """
    publisher = Publisher.query.get_or_404(publisher_id, description=f"Publisher with ID {publisher_id} not found.")

    try:
        # Check if there are any books associated with this publisher
        # Using .first() is efficient as we only need to know if at least one exists
        associated_book = Book.query.filter_by(publisher_id=publisher_id).first()
        if associated_book:
            abort(409, description=f"Cannot delete publisher '{publisher.name}' (ID: {publisher_id}) because it has associated books. Please reassign or delete the books first.")

        # If no books are associated, proceed with deletion
        db.session.delete(publisher)
        db.session.commit()
        return jsonify({"message": f"Publisher '{publisher.name}' (ID: {publisher_id}) deleted successfully."}), 200 # 200 OK or 204 No Content

    except SQLAlchemyError as e:
        db.session.rollback()
        # Log the error e
        abort(500, description=f"Database error occurred during deletion: {e}")

# --- Error Handlers for this Blueprint (Optional but Recommended) ---
# You might want global error handlers, but blueprint-specific ones can be useful too.
@publisher_bp.errorhandler(400)
def bad_request(error):
    return jsonify(error=str(error.description)), 400

@publisher_bp.errorhandler(404)
def not_found(error):
    return jsonify(error=str(error.description)), 404

@publisher_bp.errorhandler(409)
def conflict(error):
    return jsonify(error=str(error.description)), 409

@publisher_bp.errorhandler(500)
def internal_server_error(error):
    # Log the actual error internally
    print(f"Internal Server Error: {error}") # Replace with proper logging
    # Return a generic message to the client
    return jsonify(error=str(error.description) if hasattr(error, 'description') else "An internal server error occurred."), 500
