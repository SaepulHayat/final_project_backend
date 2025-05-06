from sqlalchemy import func, exc as sqlalchemy_exc
from decimal import Decimal, ROUND_HALF_UP # For accurate averaging
import logging

from ..model.rating import Rating
from ..model.user import User # Needed for relationship checks
from ..model.book import Book # Needed for relationship checks and avg rating update
from ..extensions import db
from ..utils.validators import validate_rating_input
from ..utils.response import success_response, error_response
from ..utils.roles import UserRoles # Assuming UserRoles enum

logger = logging.getLogger(__name__)

class RatingService:

    def _update_book_average_rating(self, book_id):
        """Helper function to recalculate and update the average rating for a book."""
        try:
            book = Book.query.get(book_id)
            if not book:
                logger.warning(f"Attempted to update rating for non-existent book ID: {book_id}")
                return # Or raise an error if this case shouldn't happen

            # Calculate the average score using SQLAlchemy's avg function
            # Coalesce ensures we get 0 if there are no ratings, preventing None
            avg_score_result = db.session.query(
                func.coalesce(func.avg(Rating.score), 0)
            ).filter(Rating.book_id == book_id).scalar()

            # Convert to Decimal for precise rounding (e.g., to 2 decimal places)
            avg_score_decimal = Decimal(str(avg_score_result))
            # Round to 2 decimal places (adjust precision as needed)
            rounded_avg_score = avg_score_decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            book.rating = rounded_avg_score # Update the book's rating field
            # Commit is handled by the calling function (create, update, delete)
            logger.info(f"Updated average rating for Book ID {book_id} to {book.rating}")
        except Exception as e:
            # Log the error but don't let it break the main operation if possible
            logger.error(f"Error updating average rating for Book ID {book_id}: {e}", exc_info=True)
            # Depending on requirements, you might want to re-raise or handle differently
            # db.session.rollback() # Rollback if the update itself fails critically

    def create_rating(self, book_id, user_id, data):
        errors = validate_rating_input(data)
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        book = Book.query.get(book_id)
        if not book:
            return error_response("Book not found", error="not_found", status_code=404)

        # Check if user already rated this book
        existing_rating = Rating.query.filter_by(user_id=user_id, book_id=book_id).first()
        if existing_rating:
            return error_response("User has already rated this book", error="duplicate_rating", status_code=409) # 409 Conflict

        score = data['score']
        text = data.get('text') # Optional

        new_rating = Rating(
            user_id=user_id,
            book_id=book_id,
            score=score,
            text=text
        )

        try:
            db.session.add(new_rating)
            db.session.flush() # Assign ID to new_rating
            self._update_book_average_rating(book_id) # Update average rating
            db.session.commit()
            logger.info(f"Rating created: ID {new_rating.id} for Book ID {book_id} by User ID {user_id}")
            # Use the actual to_dict() method from the model
            return success_response("Rating created successfully", data=new_rating.to_dict(), status_code=201)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating rating for Book ID {book_id} by User ID {user_id}: {e}", exc_info=True)
            return error_response("Failed to create rating", error=str(e), status_code=500)

    def get_ratings_for_book(self, book_id, args):
        book = Book.query.get(book_id)
        if not book:
            return error_response("Book not found", error="not_found", status_code=404)

        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)
        sort_by = args.get('sort_by', 'created_at') # e.g., 'score', 'created_at'
        sort_order = args.get('sort_order', 'desc') # 'asc' or 'desc'

        query = Rating.query.filter_by(book_id=book_id)

        # Sorting logic
        sort_column = getattr(Rating, sort_by, Rating.created_at) # Default to created_at
        if sort_order.lower() == 'asc':
            query = query.order_by(sort_column.asc())
        else:
            query = query.order_by(sort_column.desc())

        try:
            paginated_ratings = query.paginate(page=page, per_page=per_page, error_out=False)
            return success_response(
                "Ratings retrieved successfully",
                data={
                    # Use the actual to_dict() method from the model
                    "ratings": [r.to_dict() for r in paginated_ratings.items],
                    "total": paginated_ratings.total,
                    "pages": paginated_ratings.pages,
                    "current_page": paginated_ratings.page,
                    "book_id": book_id # Include book_id for context
                },
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error retrieving ratings for Book ID {book_id}: {e}", exc_info=True)
            return error_response("Failed to retrieve ratings", error=str(e), status_code=500)

    def get_ratings_by_user(self, user_id, args):
        user = User.query.get(user_id)
        if not user:
             return error_response("User not found", error="not_found", status_code=404)

        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)
        # Add sorting if needed, similar to get_ratings_for_book

        query = Rating.query.filter_by(user_id=user_id).order_by(Rating.created_at.desc())

        try:
            paginated_ratings = query.paginate(page=page, per_page=per_page, error_out=False)
            return success_response(
                "User ratings retrieved successfully",
                data={
                    # Use the actual to_dict() method from the model
                    "ratings": [r.to_dict() for r in paginated_ratings.items],
                    "total": paginated_ratings.total,
                    "pages": paginated_ratings.pages,
                    "current_page": paginated_ratings.page,
                    "user_id": user_id # Include user_id for context
                },
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error retrieving ratings for User ID {user_id}: {e}", exc_info=True)
            return error_response("Failed to retrieve user ratings", error=str(e), status_code=500)

    def get_rating_by_id(self, rating_id, requesting_user_id=None, requesting_user_role=None):
        rating = Rating.query.get(rating_id)
        if not rating:
            return error_response("Rating not found", error="not_found", status_code=404)

        # Optional: Check if user/seller can only view their own (if required by plan)
        # The plan allows Admin to get any, and User/Seller to view their own.
        # This check might be better placed in the route if it depends on the endpoint.
        # For a generic get_by_id service method, returning the rating might be sufficient,
        # letting the route handle authorization.
        # However, if the rule is strict:
        # if requesting_user_role != UserRoles.ADMIN and rating.user_id != requesting_user_id:
        #     return error_response("Forbidden", error="forbidden", status_code=403)

        # Use the actual to_dict() method from the model
        return success_response("Rating found", data=rating.to_dict(), status_code=200)

    def update_rating(self, rating_id, current_user_id, current_user_role, data):
        rating = Rating.query.get(rating_id)
        if not rating:
            return error_response("Rating not found", error="not_found", status_code=404)

        # Authorization Check: User/Seller can only update their own, Admin can update any
        if current_user_role != UserRoles.ADMIN and rating.user_id != current_user_id:
            return error_response("Forbidden: You can only update your own ratings", error="forbidden", status_code=403)

        errors = validate_rating_input(data, is_update=True) # Allow partial updates
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        updated = False
        if 'score' in data and data['score'] != rating.score:
            rating.score = data['score']
            updated = True
        if 'text' in data and data['text'] != rating.text:
            rating.text = data['text'] # Allow setting text to None/empty if desired
            updated = True

        if not updated:
            return error_response("No changes detected in the provided data", error="no_change", status_code=400)

        try:
            book_id = rating.book_id # Store book_id for avg update
            self._update_book_average_rating(book_id) # Update average rating
            db.session.commit()
            logger.info(f"Rating updated: ID {rating_id} by User ID {current_user_id}")
            # Use the actual to_dict() method from the model
            return success_response("Rating updated successfully", data=rating.to_dict(), status_code=200)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating rating ID {rating_id}: {e}", exc_info=True)
            return error_response("Failed to update rating", error=str(e), status_code=500)

    def delete_rating(self, rating_id, current_user_id, current_user_role):
        rating = Rating.query.get(rating_id)
        if not rating:
            return error_response("Rating not found", error="not_found", status_code=404)

         # Authorization Check: User/Seller can only delete their own, Admin can delete any
        if current_user_role != UserRoles.ADMIN and rating.user_id != current_user_id:
            return error_response("Forbidden: You can only delete your own ratings", error="forbidden", status_code=403)

        try:
            book_id = rating.book_id # Store book_id before deleting
            db.session.delete(rating)
            # Flush to ensure deletion is processed before avg calculation
            db.session.flush()
            self._update_book_average_rating(book_id) # Update average rating
            db.session.commit()
            logger.info(f"Rating deleted: ID {rating_id} by User ID {current_user_id}")
            # Service returns success dict, route handles 204 conversion
            return success_response("Rating deleted successfully", status_code=200)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting rating ID {rating_id}: {e}", exc_info=True)
            return error_response("Failed to delete rating", error=str(e), status_code=500)