# src/app/views/rating_views.py

import logging # Use logging instead of print
from flask import Blueprint, request, jsonify, g
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import joinedload

# Assuming decorators are defined elsewhere (e.g., src/app/auth/decorators.py)
# Replace these placeholders with your actual decorators
# from ..auth.decorators import login_required, role_admin, roles_required
def login_required(f):return f
def role_admin(f):return f
def role_seller(f): return f

def roles_required(*roles):
    def wrapper(f):
                return f
    return wrapper

# Import necessary components
from ..extensions import db
from ..model.rating import Rating
from ..model.book import Book
from ..model.user import User
# Import the service function
from ..services.average_rating import update_book_average_rating # Assuming the revised function is here

# Configure logger for this blueprint/module
logger = logging.getLogger(__name__)
# Basic logging config if not done elsewhere (configure properly in your app factory)
# logging.basicConfig(level=logging.INFO)


# Define the Blueprint
rating_bp = Blueprint('rating_bp', __name__)

# --- Helper Function for Serialization ---
def serialize_rating(rating):
    """Converts a Rating object into a dictionary."""
    # Ensure relationships are loaded before serialization
    username = rating.user.username if rating.user else None
    book_title = rating.book.title if rating.book else None
    return {
        "id": rating.id,
        "user_id": rating.user_id,
        "username": username,
        "book_id": rating.book_id,
        "book_title": book_title,
        "score": rating.score,
        "text": rating.text,
        "created_at": rating.created_at.isoformat(),
        "updated_at": rating.updated_at.isoformat()
    }

# --- Rating Model Endpoints ---

# POST /api/v1/books/{book_id}/ratings
@rating_bp.route('/api/v1/books/<int:book_id>/ratings', methods=['POST'])
def add_book_rating(book_id):
    """
    Add a rating/review for a specific book and update the book's average rating.
    """
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "Not Found", "message": f"Book with ID {book_id} not found."}), 404

    user_id = g.user.id

    existing_rating = Rating.query.filter_by(user_id=user_id, book_id=book_id).first()
    if existing_rating:
        return jsonify({"error": "Conflict", "message": "You have already rated this book."}), 409

    data = request.get_json()
    if not data:
        return jsonify({"error": "Bad Request", "message": "Invalid JSON payload."}), 400

    score = data.get('score')
    text = data.get('text')

    if score is None:
         return jsonify({"error": "Bad Request", "message": "Missing 'score' field."}), 400
    try:
        score = int(score)
        if not 1 <= score <= 5:
            raise ValueError("Score must be between 1 and 5.")
    except (ValueError, TypeError):
        return jsonify({"error": "Bad Request", "message": "Invalid 'score'. Must be an integer between 1 and 5."}), 400

    new_rating = Rating(
        user_id=user_id,
        book_id=book_id,
        score=score,
        text=text
    )

    try:
        # Add the new rating to the session
        db.session.add(new_rating)

        # Call the service function to update the book's rating IN THE SAME SESSION
        # Pass the session explicitly if the service function expects it
        update_success = update_book_average_rating(book_id=book_id, session=db.session)
        if not update_success:
             # Log the issue, but maybe don't fail the whole request? Or decide based on importance.
             logger.error(f"Failed to update average rating for book {book_id} after adding rating.")
             # Optionally, you could still commit the rating itself or rollback everything.
             # Let's proceed to commit the rating anyway for this example.

        # Commit the session ONCE, saving both the rating and the book update (if successful)
        db.session.commit()

        # Refresh to get DB-generated values and potentially updated relationships
        # Use options for loading relationships after refresh if needed for serialization
        db.session.refresh(new_rating)
        # Manually load relationships if refresh doesn't cascade or if they weren't loaded before add
        refreshed_rating = Rating.query.options(joinedload(Rating.user), joinedload(Rating.book))\
                                      .filter_by(id=new_rating.id).one()

        rating_data = serialize_rating(refreshed_rating)
        return jsonify(rating_data), 201

    except IntegrityError as e:
        db.session.rollback()
        logger.error(f"Database Integrity Error adding rating for book {book_id}: {e}", exc_info=True)
        return jsonify({"error": "Database Error", "message": "Could not add rating due to a database constraint."}), 500
    except SQLAlchemyError as e: # Catch broader SQLAlchemy errors during commit
        db.session.rollback()
        logger.error(f"Database Error committing rating or book update for book {book_id}: {e}", exc_info=True)
        return jsonify({"error": "Database Error", "message": "Could not save changes to the database."}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected Error adding rating for book {book_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500


# GET /api/v1/books/{book_id}/ratings (No changes needed here)
@rating_bp.route('/api/v1/books/<int:book_id>/ratings', methods=['GET'])
def list_book_ratings(book_id):
    """
    List all ratings for a specific book. Public listing.
    Supports pagination.
    Accessible by: Guest, User, Seller, Admin
    """
    book = db.session.get(Book, book_id)
    if not book:
        return jsonify({"error": "Not Found", "message": f"Book with ID {book_id} not found."}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)

    ratings_query = Rating.query.filter_by(book_id=book_id)\
                                .options(joinedload(Rating.user), joinedload(Rating.book))\
                                .order_by(Rating.created_at.desc())

    paginated_ratings = ratings_query.paginate(page=page, per_page=per_page, error_out=False)
    ratings = paginated_ratings.items

    ratings_data = [serialize_rating(rating) for rating in ratings]

    return jsonify({
        "ratings": ratings_data,
        "pagination": {
            "page": paginated_ratings.page,
            "per_page": paginated_ratings.per_page,
            "total_pages": paginated_ratings.pages,
            "total_items": paginated_ratings.total
        }
    }), 200

# GET /api/v1/ratings/users/me (No changes needed here)
@rating_bp.route('/api/v1/ratings/users/me', methods=['GET'])
def list_my_ratings():
    """
    List ratings submitted by the currently authenticated user.
    Supports pagination.
    Accessible by: Authenticated User, Seller, Admin
    """
    user_id = g.user.id
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)

    ratings_query = Rating.query.filter_by(user_id=user_id)\
                                .options(joinedload(Rating.user), joinedload(Rating.book))\
                                .order_by(Rating.created_at.desc())

    paginated_ratings = ratings_query.paginate(page=page, per_page=per_page, error_out=False)
    ratings = paginated_ratings.items
    ratings_data = [serialize_rating(rating) for rating in ratings]

    return jsonify({
        "ratings": ratings_data,
        "pagination": {
            "page": paginated_ratings.page,
            "per_page": paginated_ratings.per_page,
            "total_pages": paginated_ratings.pages,
            "total_items": paginated_ratings.total
        }
    }), 200

# GET /api/v1/ratings/users/{user_id} (No changes needed here)
@rating_bp.route('/api/v1/ratings/users/<int:user_id>', methods=['GET'])
def list_user_ratings(user_id):
    """
    List ratings submitted by a specific user.
    Supports pagination.
    Accessible by: Admin only.
    """
    target_user = db.session.get(User, user_id)
    if not target_user:
        return jsonify({"error": "Not Found", "message": f"User with ID {user_id} not found."}), 404

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    per_page = min(per_page, 100)

    ratings_query = Rating.query.filter_by(user_id=user_id)\
                                .options(joinedload(Rating.user), joinedload(Rating.book))\
                                .order_by(Rating.created_at.desc())

    paginated_ratings = ratings_query.paginate(page=page, per_page=per_page, error_out=False)
    ratings = paginated_ratings.items
    ratings_data = [serialize_rating(rating) for rating in ratings]

    return jsonify({
        "ratings": ratings_data,
        "pagination": {
            "page": paginated_ratings.page,
            "per_page": paginated_ratings.per_page,
            "total_pages": paginated_ratings.pages,
            "total_items": paginated_ratings.total
        }
    }), 200


# GET /api/v1/ratings/{rating_id} (No changes needed here)
@rating_bp.route('/api/v1/ratings/<int:rating_id>', methods=['GET'])
def get_rating_details(rating_id):
    """
    Get details of a specific rating.
    Accessible by: Admin, or the User/Seller who created it.
    """
    rating = Rating.query.options(joinedload(Rating.user), joinedload(Rating.book))\
                         .filter_by(id=rating_id).first()
    if not rating:
        return jsonify({"error": "Not Found", "message": f"Rating with ID {rating_id} not found."}), 404

    current_user_id = g.user.id
    current_user_role = g.user.role

    if current_user_role != 'Admin' and rating.user_id != current_user_id:
        return jsonify({"error": "Forbidden", "message": "You do not have permission to view this rating."}), 403

    rating_data = serialize_rating(rating)
    return jsonify(rating_data), 200

# PATCH /api/v1/ratings/{rating_id}
@rating_bp.route('/api/v1/ratings/<int:rating_id>', methods=['PATCH'])
def update_rating(rating_id):
    """
    Update a specific rating/review and update the book's average rating.
    """
    rating = db.session.get(Rating, rating_id) # Use get for primary key lookup
    if not rating:
        return jsonify({"error": "Not Found", "message": f"Rating with ID {rating_id} not found."}), 404

    # Store book_id before potential changes
    book_id_to_update = rating.book_id

    current_user_id = g.user.id
    current_user_role = g.user.role

    if current_user_role != 'Admin' and rating.user_id != current_user_id:
        return jsonify({"error": "Forbidden", "message": "You do not have permission to update this rating."}), 403

    data = request.get_json()
    if not data:
        return jsonify({"error": "Bad Request", "message": "Invalid JSON payload or empty request."}), 400

    updated = False

    if 'score' in data:
        score = data['score']
        try:
            score = int(score)
            if not 1 <= score <= 5:
                raise ValueError("Score must be between 1 and 5.")
            if rating.score != score: # Check if value actually changed
                 rating.score = score
                 updated = True
        except (ValueError, TypeError):
            return jsonify({"error": "Bad Request", "message": "Invalid 'score'. Must be an integer between 1 and 5."}), 400

    if 'text' in data:
         if rating.text != data['text']: # Check if value actually changed
            rating.text = data['text']
            updated = True

    if not updated:
        # No changes detected, maybe return the existing rating?
        # Load relationships if needed for serialization
        rating = Rating.query.options(joinedload(Rating.user), joinedload(Rating.book))\
                             .filter_by(id=rating_id).first()
        rating_data = serialize_rating(rating)
        return jsonify(rating_data), 200 # Return current data if no changes

    try:
        # Mark the rating object as dirty (implicitly done by changing attributes)
        # db.session.add(rating) # Not strictly necessary if fetched from session

        # Update the book's average rating IN THE SAME SESSION
        update_success = update_book_average_rating(book_id=book_id_to_update, session=db.session)
        if not update_success:
            logger.error(f"Failed to update average rating for book {book_id_to_update} after updating rating {rating_id}.")
            # Decide whether to proceed or rollback

        # Commit the session ONCE
        db.session.commit()

        # Refresh/reload for serialization
        # Use options for loading relationships after refresh if needed
        db.session.refresh(rating)
        refreshed_rating = Rating.query.options(joinedload(Rating.user), joinedload(Rating.book))\
                                      .filter_by(id=rating.id).one()

        rating_data = serialize_rating(refreshed_rating)
        return jsonify(rating_data), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error updating rating {rating_id} or book {book_id_to_update} rating: {e}", exc_info=True)
        return jsonify({"error": "Database Error", "message": "Could not save changes to the database."}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected Error updating rating {rating_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500

# DELETE /api/v1/ratings/{rating_id}
@rating_bp.route('/api/v1/ratings/<int:rating_id>', methods=['DELETE'])
def delete_rating(rating_id):
    """
    Delete a specific rating/review and update the book's average rating.
    """
    rating = db.session.get(Rating, rating_id)
    if not rating:
        return jsonify({"error": "Not Found", "message": f"Rating with ID {rating_id} not found."}), 404

    # Get associated book_id BEFORE deleting the rating
    book_id_to_update = rating.book_id

    current_user_id = g.user.id
    current_user_role = g.user.role

    if current_user_role != 'Admin' and rating.user_id != current_user_id:
        return jsonify({"error": "Forbidden", "message": "You do not have permission to delete this rating."}), 403

    try:
        # Delete the rating object from the session
        db.session.delete(rating)

        # Update the book's average rating IN THE SAME SESSION
        update_success = update_book_average_rating(book_id=book_id_to_update, session=db.session)
        if not update_success:
             logger.error(f"Failed to update average rating for book {book_id_to_update} after deleting rating {rating_id}.")
             # Decide whether to proceed or rollback

        # Commit the session ONCE
        db.session.commit()

        return jsonify({"message": f"Rating with ID {rating_id} deleted successfully."}), 200

    except SQLAlchemyError as e:
        db.session.rollback()
        logger.error(f"Database error deleting rating {rating_id} or updating book {book_id_to_update} rating: {e}", exc_info=True)
        return jsonify({"error": "Database Error", "message": "Could not save changes to the database."}), 500
    except Exception as e:
        db.session.rollback()
        logger.error(f"Unexpected Error deleting rating {rating_id}: {e}", exc_info=True)
        return jsonify({"error": "Internal Server Error", "message": "An unexpected error occurred."}), 500

