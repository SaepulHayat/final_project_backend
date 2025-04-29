from sqlalchemy import func
from ..model.book import Book
from ..model.rating import Rating
from ..extensions import db

def update_book_rating(book_id: int):
    """
    Calculates the average rating for a given book_id from the Rating table
    and updates the rating field in the Book table.

    Args:
        book_id: The ID of the book to update.
    """
    try:
        average_rating = db.session.query(func.avg(Rating.score))\
                                   .filter(Rating.book_id == book_id)\
                                   .scalar()

        book = db.session.get(Book, book_id)

        if book:
            if average_rating is not None:
                book.rating = round(average_rating, 2)
            else:
                book.rating = None 

            db.session.commit()
            print(f"Successfully updated rating for Book ID {book_id} to {book.rating}")

        else:
            print(f"Book with ID {book_id} not found.")

    except Exception as e:
        db.session.rollback()
        print(f"An error occurred while updating rating for Book ID {book_id}: {e}")
