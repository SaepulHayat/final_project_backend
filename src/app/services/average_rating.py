# ./services/average_rating.py
import logging
from sqlalchemy import func
from sqlalchemy.exc import SQLAlchemyError
from ..model.book import Book
from ..model.rating import Rating
# Assuming db is imported from extensions and logger is configured elsewhere
from ..extensions import db

# Configure a logger for this module (or use a central app logger)
logger = logging.getLogger(__name__)

def update_book_average_rating(book_id: int, session=db.session):
    """
    Calculates the average rating for a given book_id and updates the
    rating field on the Book object within the provided session.
    Does NOT commit the session itself.

    Args:
        book_id: The ID of the book to update.
        session: The SQLAlchemy session object to use. Defaults to db.session.

    Returns:
        bool: True if the update was successful (or no update needed),
              False if an error occurred or the book was not found.
    """
    try:
        # 1. Fetch the book first
        book = session.get(Book, book_id)

        if not book:
            logger.warning(f"Book with ID {book_id} not found for rating update.")
            return False # Indicate book not found

        # 2. Calculate average rating only if book exists
        average_rating = session.query(func.avg(Rating.score))\
                                .filter(Rating.book_id == book_id)\
                                .scalar()

        # 3. Update the book object (no commit here)
        new_rating = None
        if average_rating is not None:
            # Round to match the Numeric(3, 2) precision
            new_rating = round(average_rating, 2)

        # Only update if the value changes to avoid unnecessary writes
        if book.rating != new_rating:
            book.rating = new_rating
            logger.info(f"Updating rating for Book ID {book_id} to {book.rating} in session.")
            # Mark the object as dirty, session.commit() later will save it.
            session.add(book)
        else:
            logger.info(f"Rating for Book ID {book_id} is already {book.rating}. No update needed.")

        return True # Indicate success (update prepared or not needed)

    except SQLAlchemyError as e:
        # Rollback should happen in the calling context if an error occurs there
        logger.error(f"Database error updating rating for Book ID {book_id}: {e}", exc_info=True)
        return False # Indicate failure
    except Exception as e:
        # Catching other potential errors (e.g., rounding issues, though unlikely)
        logger.error(f"Unexpected error updating rating for Book ID {book_id}: {e}", exc_info=True)
        return False # Indicate failure