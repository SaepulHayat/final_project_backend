# src/app/views/category_views.py

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from ..extensions import db

def login_required(f): return f
def role_admin(f): return f

# Import necessary models
from ..model.category import Category
from ..model.book import Book # For listing books by category

# Create Blueprint
# Assumes this blueprint will be registered with the Flask app elsewhere
category_bp = Blueprint('category_bp', __name__, url_prefix='/api/v1/categories')

# --- Helper Function for Serialization (Optional but Recommended) ---
def serialize_category(category):
    """Converts a Category object into a dictionary."""
    return {
        "id": category.id,
        "name": category.name,
        "created_at": category.created_at.isoformat() if category.created_at else None,
        "updated_at": category.updated_at.isoformat() if category.updated_at else None
    }

def serialize_book_summary(book):
    """Converts a Book object into a summary dictionary for lists."""
    # Adjust fields as needed for the book summary
    return {
        "id": book.id,
        "title": book.title,
        "author_id": book.author_id, # Assuming direct author_id is sufficient here
        "price": float(book.price) if book.price is not None else None, # Convert Decimal
        "rating": float(book.rating) if book.rating is not None else None, # Convert Decimal
        "image_url_1": book.image_url_1
    }

# --- Category Model Endpoints ---

# POST /api/v1/categories/ (Admin)
@category_bp.route('/', methods=['POST'])
@login_required
@role_admin
def add_category():
    """
    Add a new category.
    Accessible by: Admin
    """
    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "Missing 'name' in request body"}), 400

    category_name = data['name'].strip()
    if not category_name:
        return jsonify({"error": "'name' cannot be empty"}), 400

    # Check if category already exists (case-insensitive check might be better)
    existing_category = Category.query.filter(Category.name.ilike(category_name)).first()
    if existing_category:
        return jsonify({"error": f"Category '{category_name}' already exists"}), 409 # Conflict

    new_category = Category(name=category_name)

    try:
        db.session.add(new_category)
        db.session.commit()
        return jsonify(serialize_category(new_category)), 201 # Created
    except IntegrityError as e: # Catch potential unique constraint violations again
        db.session.rollback()
        # Log the error e
        print(f"IntegrityError: {e}")
        return jsonify({"error": "Database integrity error. Category might already exist."}), 409
    except SQLAlchemyError as e: # Catch other potential DB errors
        db.session.rollback()
        # Log the error e
        print(f"SQLAlchemyError: {e}")
        return jsonify({"error": "Database error occurred while adding category"}), 500
    except Exception as e: # Catch unexpected errors
        db.session.rollback()
        # Log the error e
        print(f"Unexpected Error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# GET /api/v1/categories/ (Guest, User, Seller, Admin)
@category_bp.route('/', methods=['GET'])
def list_categories():
    """
    List all categories. Public listing.
    Accessible by: Guest, User, Seller, Admin
    """
    try:
        # Basic pagination (optional, adjust as needed)
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 100) # Limit max per_page

        categories_query = Category.query.order_by(Category.name)
        paginated_categories = categories_query.paginate(page=page, per_page=per_page, error_out=False)

        results = [serialize_category(cat) for cat in paginated_categories.items]

        return jsonify({
            "categories": results,
            "total": paginated_categories.total,
            "pages": paginated_categories.pages,
            "current_page": page,
            "per_page": per_page
        }), 200
    except SQLAlchemyError as e:
        print(f"SQLAlchemyError: {e}")
        return jsonify({"error": "Database error occurred while fetching categories"}), 500
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# GET /api/v1/categories/{category_id} (Guest, User, Seller, Admin)
@category_bp.route('/<int:category_id>', methods=['GET'])
def get_category_details(category_id):
    """
    Get details of a specific category. Public detail view.
    Accessible by: Guest, User, Seller, Admin
    """
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({"error": f"Category with id {category_id} not found"}), 404

        return jsonify(serialize_category(category)), 200
    except SQLAlchemyError as e:
        print(f"SQLAlchemyError: {e}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# GET /api/v1/categories/{category_id}/books (Guest, User, Seller, Admin)
@category_bp.route('/<int:category_id>/books', methods=['GET'])
def list_books_by_category(category_id):
    """
    List books within a specific category.
    Accessible by: Guest, User, Seller, Admin
    """
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({"error": f"Category with id {category_id} not found"}), 404

        # Basic pagination
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        per_page = min(per_page, 50) # Limit max per_page for book lists

        # Access books through the relationship, apply pagination
        # Note: This loads all books then slices. For very large categories,
        # consider optimizing the query if performance becomes an issue.
        books_query = Book.query.with_parent(category).order_by(Book.title)
        paginated_books = books_query.paginate(page=page, per_page=per_page, error_out=False)

        results = [serialize_book_summary(book) for book in paginated_books.items]

        return jsonify({
            "category": serialize_category(category), # Include category info
            "books": results,
            "total_books_in_category": paginated_books.total,
            "pages": paginated_books.pages,
            "current_page": page,
            "per_page": per_page
        }), 200
    except SQLAlchemyError as e:
        print(f"SQLAlchemyError: {e}")
        return jsonify({"error": "Database error occurred"}), 500
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# PATCH /api/v1/categories/{category_id} (Admin)
@category_bp.route('/<int:category_id>', methods=['PATCH'])
@login_required
@role_admin
def update_category_details(category_id):
    """
    Update a category's details (e.g., name).
    Accessible by: Admin
    """
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({"error": f"Category with id {category_id} not found"}), 404

        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({"error": "Missing 'name' in request body"}), 400

        new_name = data['name'].strip()
        if not new_name:
            return jsonify({"error": "'name' cannot be empty"}), 400

        # Check if the new name conflicts with another existing category
        existing_category = Category.query.filter(Category.name.ilike(new_name), Category.id != category_id).first()
        if existing_category:
            return jsonify({"error": f"Another category with the name '{new_name}' already exists"}), 409 # Conflict

        # Update the name if it's different
        if category.name != new_name:
            category.name = new_name
            # updated_at is handled automatically by server_onupdate

        db.session.commit()
        return jsonify(serialize_category(category)), 200

    except IntegrityError as e: # Catch potential unique constraint violations
        db.session.rollback()
        print(f"IntegrityError: {e}")
        return jsonify({"error": "Database integrity error. The name might already exist."}), 409
    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"SQLAlchemyError: {e}")
        return jsonify({"error": "Database error occurred while updating category"}), 500
    except Exception as e:
        db.session.rollback()
        print(f"Unexpected Error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500


# DELETE /api/v1/categories/{category_id} (Admin)
@category_bp.route('/<int:category_id>', methods=['DELETE'])
@login_required
@role_admin
def delete_category(category_id):
    """
    Delete a category. Prevents deletion if books are associated with it.
    Accessible by: Admin
    """
    try:
        category = Category.query.get(category_id)
        if not category:
            return jsonify({"error": f"Category with id {category_id} not found"}), 404

        # Check if any books are associated with this category
        # Accessing category.books performs a query
        if category.books: # Check if the list is not empty
             # Count associated books for a more informative message (optional)
            book_count = Book.query.with_parent(category).count()
            if book_count > 0:
                return jsonify({
                    "error": f"Cannot delete category '{category.name}' because it is associated with {book_count} book(s). Please disassociate books first."
                }), 409 # Conflict - cannot delete due to dependencies

        # If no books are associated, proceed with deletion
        db.session.delete(category)
        db.session.commit()
        return jsonify({"message": f"Category '{category.name}' (ID: {category_id}) deleted successfully"}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        print(f"SQLAlchemyError: {e}")
        return jsonify({"error": "Database error occurred while deleting category"}), 500
    except Exception as e:
        db.session.rollback()
        print(f"Unexpected Error: {e}")
        return jsonify({"error": "An unexpected error occurred"}), 500
