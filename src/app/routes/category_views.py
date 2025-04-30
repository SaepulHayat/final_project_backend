# src/app/views/category_views.py

from flask import Blueprint, request, jsonify
from sqlalchemy.exc import IntegrityError
from ..extensions import db  # Assuming db is initialized in extensions
from ..model.category import Category
from ..model.book import Book # For listing books by category

# Placeholder decorators - replace with actual implementations if needed
# from ..auth.decorators import login_required, role_admin
def login_required(f): return f
def role_admin(f): return f
# def roles_required(*roles):
#     def wrapper(f):
#         return f
#     return wrapper

# Create Blueprint
category_bp = Blueprint('category_bp', __name__, url_prefix='/api/v1/categories')

# --- Helper Function for Serialization (Simple Example) ---
def serialize_category(category):
    """Converts a Category object to a dictionary."""
    return {
        'id': category.id,
        'name': category.name,
        'created_at': category.created_at.isoformat(),
        'updated_at': category.updated_at.isoformat()
    }

def serialize_book_simple(book):
    """Converts a Book object to a simple dictionary for lists."""
    return {
        'id': book.id,
        'title': book.title,
        'price': str(book.price) # Convert Decimal to string for JSON
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
    Requires JSON body: {"name": "Category Name"}
    """
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"error": "Category name is required"}), 400

    name = data['name'].strip()
    if not name:
        return jsonify({"error": "Category name cannot be empty"}), 400

    # Check if category already exists (case-insensitive check might be better in some cases)
    existing_category = db.session.execute(db.select(Category).filter_by(name=name)).scalar_one_or_none()
    if existing_category:
        return jsonify({"error": f"Category with name '{name}' already exists"}), 409 # Conflict

    new_category = Category(name=name)

    try:
        db.session.add(new_category)
        db.session.commit()
        return jsonify(serialize_category(new_category)), 201 # Created
    except IntegrityError as e:
        db.session.rollback()
        # This might happen due to race conditions if the initial check passes
        return jsonify({"error": "Database integrity error, possibly duplicate name", "details": str(e)}), 500
    except Exception as e:
        db.session.rollback()
        # Log the exception e
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


# GET /api/v1/categories/ (Guest, User, Seller, Admin)
@category_bp.route('/', methods=['GET'])
def list_categories():
    """
    List all categories. Public listing.
    Accessible by: Guest, User, Seller, Admin
    """
    try:
        # Consider adding pagination for large numbers of categories
        # page = request.args.get('page', 1, type=int)
        # per_page = request.args.get('per_page', 10, type=int)
        # categories_query = db.select(Category).order_by(Category.name)
        # categories_page = db.paginate(categories_query, page=page, per_page=per_page, error_out=False)
        # categories = categories_page.items

        categories = db.session.execute(db.select(Category).order_by(Category.name)).scalars().all()
        return jsonify([serialize_category(cat) for cat in categories]), 200
    except Exception as e:
        # Log the exception e
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500

# GET /api/v1/categories/{category_id} (Guest, User, Seller, Admin)
@category_bp.route('/<int:category_id>', methods=['GET'])
def get_category_details(category_id):
    """
    Get details of a specific category. Public detail view.
    Accessible by: Guest, User, Seller, Admin
    """
    try:
        # get_or_404 simplifies checking if the category exists
        category = db.get_or_404(Category, category_id, description=f"Category with id {category_id} not found")
        return jsonify(serialize_category(category)), 200
    except Exception as e:
         # Log the exception e (already handled by get_or_404 for Not Found)
        if hasattr(e, 'code') and e.code == 404:
             raise e # Re-raise Werkzeug NotFound exception
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


# GET /api/v1/categories/{category_id}/books (Guest, User, Seller, Admin)
@category_bp.route('/<int:category_id>/books', methods=['GET'])
def list_books_by_category(category_id):
    """
    List books within a specific category.
    Accessible by: Guest, User, Seller, Admin
    """
    try:
        category = db.get_or_404(Category, category_id, description=f"Category with id {category_id} not found")

        # Access books via the relationship
        # Consider pagination if a category can have many books
        books_in_category = category.books # This uses the relationship defined in the model

        return jsonify([serialize_book_simple(book) for book in books_in_category]), 200
    except Exception as e:
        if hasattr(e, 'code') and e.code == 404:
             raise e # Re-raise Werkzeug NotFound exception
        # Log the exception e
        return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500


# PATCH /api/v1/categories/{category_id} (Admin)
@category_bp.route('/<int:category_id>', methods=['PATCH'])
@login_required
@role_admin
def update_category_details(category_id):
    """
    Update a category's details (only name currently).
    Accessible by: Admin
    Requires JSON body: {"name": "Updated Category Name"}
    """
    category = db.get_or_404(Category, category_id, description=f"Category with id {category_id} not found")

    data = request.get_json()
    if not data or 'name' not in data:
        return jsonify({"error": "No update data provided or 'name' field missing"}), 400

    new_name = data.get('name', '').strip()
    if not new_name:
         return jsonify({"error": "Category name cannot be empty"}), 400

    # Check if the new name conflicts with another existing category
    if new_name != category.name:
        existing_category = db.session.execute(
            db.select(Category).filter(Category.name == new_name, Category.id != category_id)
        ).scalar_one_or_none()
        if existing_category:
            return jsonify({"error": f"Another category with name '{new_name}' already exists"}), 409 # Conflict

        category.name = new_name

        try:
            db.session.commit()
            return jsonify(serialize_category(category)), 200
        except IntegrityError as e:
            db.session.rollback()
            return jsonify({"error": "Database integrity error, possibly duplicate name", "details": str(e)}), 500
        except Exception as e:
            db.session.rollback()
            # Log the exception e
            return jsonify({"error": "An unexpected error occurred", "details": str(e)}), 500
    else:
        # Name hasn't changed, return current data
        return jsonify(serialize_category(category)), 200


# DELETE /api/v1/categories/{category_id} (Admin)
@category_bp.route('/<int:category_id>', methods=['DELETE'])
@login_required
@role_admin
def delete_category(category_id):
    """
    Delete a category. Prevents deletion if books are associated with it.
    Accessible by: Admin
    """
    category = db.get_or_404(Category, category_id, description=f"Category with id {category_id} not found")

    # Strategy: Prevent deletion if books are associated
    if category.books:
        return jsonify({
            "error": f"Cannot delete category '{category.name}' because it is associated with one or more books.",
            "book_count": len(category.books) # Optionally provide count
        }), 409 # Conflict

    try:
        db.session.delete(category)
        db.session.commit()
        return jsonify({"message": f"Category '{category.name}' (ID: {category_id}) deleted successfully"}), 200 # OK
        # return '', 204 # No Content is also a valid response for DELETE
    except Exception as e:
        db.session.rollback()
        # Log the exception e
        return jsonify({"error": "An unexpected error occurred during deletion", "details": str(e)}), 500

