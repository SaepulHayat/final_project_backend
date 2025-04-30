# src/app/views/author_views.py

import logging # Import the logging library
from flask import Blueprint, request, jsonify, abort
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload # Optional: for eager loading books

# Import database session and models
from ..extensions import db
from ..model.author import Author
from ..model.book import Book

# Configure basic logging
logging.basicConfig(level=logging.INFO) # You might want more sophisticated logging config

# Assuming decorators are defined elsewhere and handle authentication/authorization
# from ..auth.decorators import login_required, role_admin, role_seller, roles_required
# Placeholder decorators for demonstration
def login_required(f): return f
def role_admin(f): return f
def role_seller(f): return f
def roles_required(f): return f

# Create Blueprint
author_bp = Blueprint('author_bp', __name__, url_prefix='/api/v1/authors')

# --- Helper Function for Serialization ---
def serialize_author(author, include_books=False):
    """Converts an Author object into a dictionary."""
    data = {
        'id': author.id,
        'first_name': author.first_name,
        'last_name': author.last_name,
        'bio': author.bio,
        'created_at': author.created_at.isoformat() if author.created_at else None,
        'updated_at': author.updated_at.isoformat() if author.updated_at else None,
    }
    # Optionally include basic book info (adjust serialization as needed)
    if include_books:
         # Use the relationship directly. Assumes Book has a simple serialize method or similar logic.
        data['books'] = [
            {'id': book.id, 'title': book.title}
            for book in author.books # Access the relationship
        ]
    return data

def serialize_book_simple(book):
    """Converts a Book object into a simple dictionary for lists."""
    return {
        'id': book.id,
        'title': book.title,
        'price': str(book.price) if book.price is not None else None, # Convert Decimal to string
        'author_id': book.author_id # Include author_id
    }

# --- Author Model Endpoints ---

# POST /api/v1/authors/ (Admin, Seller)
@author_bp.route('/', methods=['POST'])
@login_required
@roles_required('Admin', 'Seller')
def add_author():
    """
    Add a new author.
    Accessible by: Admin, Seller
    """
    data = request.get_json()
    if not data or not data.get('first_name'):
        abort(400, description="Missing required field: first_name.")

    first_name = data.get('first_name')
    last_name = data.get('last_name')
    bio = data.get('bio')

    # Optional: Check for duplicate author (based on name)
    # Consider making this check case-insensitive if appropriate
    existing_author = Author.query.filter(
        db.func.lower(Author.first_name) == db.func.lower(first_name),
        db.func.lower(Author.last_name) == db.func.lower(last_name) # Handle potential None for last_name
    ).first()
    if existing_author:
        logging.warning(f"Attempt to add duplicate author: {first_name} {last_name}")
        return jsonify({"error": "Author with this name already exists", "author_id": existing_author.id}), 409 # Conflict

    new_author = Author(
        first_name=first_name,
        last_name=last_name,
        bio=bio
    )

    try:
        db.session.add(new_author)
        db.session.commit()
        logging.info(f"Author added successfully: ID {new_author.id}, Name: {first_name} {last_name}")
        return jsonify(serialize_author(new_author)), 201
    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Database integrity error while adding author '{first_name} {last_name}': {e}", exc_info=True)
        abort(500, description=f"Database error occurred while adding author. Integrity constraint violated: {e}") # Provide more specific info if safe
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error while adding author '{first_name} {last_name}': {e}", exc_info=True)
        abort(500, description="An unexpected error occurred while adding the author.")


# GET /api/v1/authors/ (Guest, User, Seller, Admin)
@author_bp.route('/', methods=['GET'])
def list_authors():
    """
    List all authors (paginated, searchable by name). Public listing.
    Accessible by: Guest, User, Seller, Admin
    """
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    search_term = request.args.get('search', None, type=str)

    query = Author.query.order_by(Author.first_name, Author.last_name)

    if search_term:
        # Simple search across first and last names (case-insensitive)
        search_filter = f"%{search_term}%"
        query = query.filter(
            (Author.first_name.ilike(search_filter)) |
            (Author.last_name.ilike(search_filter))
        )

    try:
        paginated_authors = query.paginate(page=page, per_page=per_page, error_out=False)
        authors_data = [serialize_author(author) for author in paginated_authors.items]

        return jsonify({
            'authors': authors_data,
            'total': paginated_authors.total,
            'pages': paginated_authors.pages,
            'current_page': paginated_authors.page,
            'per_page': paginated_authors.per_page,
            'has_next': paginated_authors.has_next,
            'has_prev': paginated_authors.has_prev
        }), 200
    except Exception as e:
        logging.error(f"Error retrieving author list: {e}", exc_info=True)
        abort(500, description="An error occurred while retrieving authors.")


# GET /api/v1/authors/{author_id} (Guest, User, Seller, Admin)
@author_bp.route('/<int:author_id>', methods=['GET'])
def get_author_details(author_id):
    """
    Get details of a specific author. Public detail view.
    Accessible by: Guest, User, Seller, Admin
    """
    try:
        # Optional: Use joinedload to fetch books efficiently if include_books=True
        # author = Author.query.options(joinedload(Author.books)).get_or_404(author_id)
        author = Author.query.get_or_404(author_id, description=f"Author with ID {author_id} not found.")
        # Set include_books=True if you want to include book list here
        return jsonify(serialize_author(author, include_books=False)), 200
    except Exception as e:
         # Catch potential errors during serialization or other issues
        logging.error(f"Error retrieving details for author {author_id}: {e}", exc_info=True)
        # get_or_404 handles not found, so this is likely a 500
        abort(500, description=f"An error occurred while retrieving details for author {author_id}.")


# GET /api/v1/authors/{author_id}/books (Guest, User, Seller, Admin)
@author_bp.route('/<int:author_id>/books', methods=['GET'])
def list_books_by_author(author_id):
    """
    List books by a specific author (paginated).
    Accessible by: Guest, User, Seller, Admin
    """
    # First, check if the author exists
    author = Author.query.get_or_404(author_id, description=f"Author with ID {author_id} not found.")

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # Query books directly using the relationship or filtering Book model
    # Option 1: Using the relationship (potentially less efficient for pagination if not lazy='dynamic')
    # query = author.books # If lazy='dynamic', this returns a query object

    # Option 2: Filtering the Book model directly (generally better for pagination)
    query = Book.query.filter(Book.author_id == author_id).order_by(Book.title)

    try:
        paginated_books = query.paginate(page=page, per_page=per_page, error_out=False)
        books_data = [serialize_book_simple(book) for book in paginated_books.items]

        return jsonify({
            'books': books_data,
            'author_id': author_id,
            'total': paginated_books.total,
            'pages': paginated_books.pages,
            'current_page': paginated_books.page,
            'per_page': paginated_books.per_page,
            'has_next': paginated_books.has_next,
            'has_prev': paginated_books.has_prev
        }), 200
    except Exception as e:
        logging.error(f"Error retrieving book list for author {author_id}: {e}", exc_info=True)
        abort(500, description=f"An error occurred while retrieving books for author {author_id}.")


# PATCH /api/v1/authors/{author_id} (Admin)
@author_bp.route('/<int:author_id>', methods=['PATCH'])
@login_required
@role_admin
def update_author_details(author_id):
    """
    Update an author's details.
    Accessible by: Admin
    """
    author = Author.query.get_or_404(author_id, description=f"Author with ID {author_id} not found.")
    data = request.get_json()

    if not data:
        abort(400, description="No update data provided.")

    updated_fields = [] # Keep track of what was changed

    # Update fields if they are present in the request data
    if 'first_name' in data and data['first_name'] != author.first_name:
        author.first_name = data['first_name']
        updated_fields.append('first_name')
    if 'last_name' in data and data['last_name'] != author.last_name:
        author.last_name = data['last_name']
        updated_fields.append('last_name')
    if 'bio' in data and data['bio'] != author.bio:
        author.bio = data['bio']
        updated_fields.append('bio')

    if not updated_fields:
         return jsonify({"message": "No changes detected or applied."}), 200 # Or 304 Not Modified

    # Optional: Check for potential name conflicts if name is updated
    if 'first_name' in updated_fields or 'last_name' in updated_fields:
         existing_author = Author.query.filter(
             Author.id != author_id, # Exclude the current author
             db.func.lower(Author.first_name) == db.func.lower(author.first_name),
             db.func.lower(Author.last_name) == db.func.lower(author.last_name) # Handle potential None
         ).first()
         if existing_author:
             # Don't rollback yet, just inform the user
             return jsonify({"error": "Another author with this updated name already exists"}), 409

    try:
        db.session.commit()
        logging.info(f"Author {author_id} updated fields: {', '.join(updated_fields)}")
        return jsonify(serialize_author(author)), 200
    except IntegrityError as e:
        db.session.rollback()
        logging.error(f"Database integrity error while updating author {author_id}: {e}", exc_info=True)
        abort(500, description=f"Database error occurred during update. Integrity constraint violated: {e}")
    except Exception as e:
        db.session.rollback()
        logging.error(f"Unexpected error while updating author {author_id}: {e}", exc_info=True)
        abort(500, description="An unexpected error occurred during update.")


# DELETE /api/v1/authors/{author_id} (Admin)
@author_bp.route('/<int:author_id>', methods=['DELETE'])
@login_required
@role_admin
def delete_author(author_id):
    """
    Delete an author and set author_id to NULL for associated books.
    IMPORTANT: Requires Book.author_id to be nullable=True in the model
               and the corresponding database schema change applied via migration.
    Accessible by: Admin
    """
    author = Author.query.get_or_404(author_id, description=f"Author with ID {author_id} not found.")
    author_name = f"{author.first_name} {author.last_name}" # For logging

    # --- Strategy Decision: Option 3 ---
    # Set book.author_id to NULL (Requires author_id to be nullable in Book model)
    try:
        # Perform the update on associated books first
        updated_count = Book.query.filter(Book.author_id == author_id).update({Book.author_id: None})
        logging.info(f"Set author_id to NULL for {updated_count} books associated with author {author_id} ({author_name}).")

        # Now delete the author
        db.session.delete(author)
        db.session.commit() # Commit both the update and the delete
        logging.info(f"Author {author_id} ({author_name}) deleted successfully after disassociating books.")
        # Standard practice is to return 204 No Content on successful DELETE
        return '', 204
    except Exception as e:
        db.session.rollback()
        logging.error(f"Error deleting author {author_id} ({author_name}) or disassociating books: {e}", exc_info=True)
        abort(500, description=f"An error occurred while deleting author {author_id} or updating associated books.")

