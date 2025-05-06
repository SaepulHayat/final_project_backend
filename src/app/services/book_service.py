from decimal import Decimal, ROUND_HALF_UP # For price validation and rating
from flask_jwt_extended import get_jwt_identity # To get current user ID
from sqlalchemy import func # For average calculation
from sqlalchemy.orm import joinedload, subqueryload # For eager loading
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..model.book import Book
from ..model.author import Author
from ..model.publisher import Publisher
from ..model.category import Category
from ..model.user import User # Import User model
from ..model.rating import Rating # Needed for average calculation
from ..model.location import Location # Import Location model
from ..model.city import City # Import City model
from ..model.state import State # Import State model
from ..model.country import Country # Import Country model
from ..utils.validators import validate_book_input
from ..utils.response import success_response, error_response
import logging

logger = logging.getLogger(__name__)

class BookService:

    def _get_and_validate_related(self, data):
        """Helper to fetch and validate related entities (Author, Publisher, Categories)."""
        related = {'author': None, 'publisher': None, 'categories': []}
        errors = {}

        author_id = data.get('author_id')
        if author_id:
            related['author'] = Author.query.get(author_id)
            if not related['author']:
                errors['author_id'] = f"Author with ID {author_id} not found."

        publisher_id = data.get('publisher_id')
        if publisher_id:
            related['publisher'] = Publisher.query.get(publisher_id)
            if not related['publisher']:
                errors['publisher_id'] = f"Publisher with ID {publisher_id} not found."

        category_ids = data.get('category_ids', [])
        if category_ids:
            if not isinstance(category_ids, list):
                errors['category_ids'] = "Category IDs must be a list."
            else:
                categories = Category.query.filter(Category.id.in_(category_ids)).all()
                if len(categories) != len(set(category_ids)): # Check if all provided IDs were
                    found_ids = {cat.id for cat in categories}
                    missing_ids = [cid for cid in category_ids if cid not in found_ids]
                    errors['category_ids'] = f"Categories with IDs {missing_ids} not found."
                else:
                    related['categories'] = categories # Assign list of Category objects

        return related, errors


    def _update_book_average_rating(self, book_id):
        """
        Helper function to recalculate and update the average rating for a book.
        This should be called within the same transaction whenever a Rating
        for this book is created, updated, or deleted (likely from a RatingService).
        """
        try:
            book = Book.query.get(book_id)
            if not book:
                logger.warning(f"Attempted to update rating for non-existent book ID: {book_id}")
                return

            avg_score_result = db.session.query(
                func.coalesce(func.avg(Rating.score), 0)
            ).filter(Rating.book_id == book_id).scalar()

            avg_score_decimal = Decimal(str(avg_score_result))
            rounded_avg_score = avg_score_decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            book.rating = rounded_avg_score
            logger.info(f"Updated average rating for Book ID {book_id} to {book.rating}")
        except Exception as e:
            logger.error(f"Error updating average rating for Book ID {book_id}: {e}", exc_info=True)
            # Let the calling function handle transaction management.

    def create_book(self, data, user_id):
        # 1. Get User (who will be the seller/owner of the book)
        user = User.query.get(user_id)
        if not user:
            # This case might be less likely if jwt_required worked, but good practice
            return error_response("User not found.", error="unauthorized", status_code=401)

        # --- BEGIN MODIFICATION ---
        # Validate if the user has a location_id set
        if not user.location_id:
            logger.warning(f"User ID {user_id} attempted to create a book without a location_id.")
            return error_response(
                "You must set your location before listing a book for sale. Please update your profile with a location.",
                error="location_required",
                status_code=400  # Bad Request, as a prerequisite is missing
            )
        # --- END MODIFICATION ---

        # Optional: Check if user role allows creating books (e.g., 'seller', 'admin')
        # if user.role not in ['seller', 'admin']:
        #    return error_response("User role not permitted to create books.", error="forbidden", status_code=403)

        # 2. Validate Input Data
        errors = validate_book_input(data)
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        # 3. Fetch and Validate Related Entities (Author, Publisher, Categories)
        related_entities, related_errors = self._get_and_validate_related(data)
        if related_errors:
            errors = (errors or {}) | related_errors
            return error_response("Validation failed", errors=errors, status_code=400)

        # 4. Create Book Instance (Initialize rating to None or 0)
        new_book = Book(
            title=data['title'],
            description=data.get('description'),
            quantity=data['quantity'],
            price=Decimal(str(data['price'])), # Ensure conversion to Decimal
            discount_percent=data.get('discount_percent', 0),
            image_url_1=data.get('image_url_1'),
            image_url_2=data.get('image_url_2'),
            image_url_3=data.get('image_url_3'),
            user_id=user.id, # Assign the logged-in user's ID
            author=related_entities['author'],
            publisher=related_entities['publisher'],
            rating=None # Initialize rating
        )

        # 5. Add Categories
        if related_entities['categories']:
            new_book.categories.extend(related_entities['categories'])


        # 6. Add to Session and Commit
        try:
            db.session.add(new_book)
            db.session.commit()
            logger.info(f"Book created: ID {new_book.id}, Title '{new_book.title}', User ID {user.id}")
            # Use the corrected to_dict method for the response
            return success_response("Book created successfully", data=new_book.to_dict(), status_code=201)
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Integrity error creating book '{data['title']}': {e}", exc_info=True)
            return error_response("Failed to create book due to database constraint.", error="db_integrity_error", status_code=409)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating book '{data['title']}': {e}", exc_info=True)
            return error_response("Failed to create book", error=str(e), status_code=500)

    def get_all_books(self, args):
        # (Uses Book.rating for sorting if specified)
        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 12, type=int)
        search_term = args.get('search')
        author_id = args.get('author_id', type=int)
        publisher_id = args.get('publisher_id', type=int)
        category_id = args.get('category_id', type=int)
        user_id_filter = args.get('user_id', type=int) # Filter by user who listed the book
        min_price = args.get('min_price', type=float)
        max_price = args.get('max_price', type=float)
        sort_by = args.get('sort_by', 'created_at')
        order = args.get('order', 'desc')

        # Eager load related entities including the user and their location details
        query = Book.query.options(
            joinedload(Book.author),
            joinedload(Book.publisher),
            joinedload(Book.user).joinedload(User.location).joinedload(Location.city).joinedload(City.state).joinedload(State.country), # Load user and their full location path
            subqueryload(Book.categories)
        )

        # Filtering

        if search_term: query = query.filter(Book.title.ilike(f'%{search_term}%'))
        if author_id: query = query.filter(Book.author_id == author_id)
        if publisher_id: query = query.filter(Book.publisher_id == publisher_id)
        if category_id: query = query.filter(Book.categories.any(Category.id == category_id))
        if user_id_filter: query = query.filter(Book.user_id == user_id_filter) # Filter by user
        if min_price is not None: query = query.filter(Book.price >= Decimal(str(min_price)))
        if max_price is not None: query = query.filter(Book.price <= Decimal(str(max_price)))

        # Sorting (remains the same, uses Book.rating)
        order_direction = db.desc if order.lower() == 'desc' else db.asc
        if sort_by == 'price':
            query = query.order_by(order_direction(Book.price))
        elif sort_by == 'title':
            query = query.order_by(order_direction(Book.title))
        elif sort_by == 'rating':
           query = query.order_by(order_direction(Book.rating))
        else: # Default sort by creation date
            query = query.order_by(order_direction(Book.created_at))

        try:
            paginated_books = query.paginate(page=page, per_page=per_page, error_out=False)
            return success_response(
                "Books retrieved successfully",
                data={
                    # Use the corrected to_simple_dict method
                    "books": [book.to_simple_dict() for book in paginated_books.items],
                    "total": paginated_books.total,
                    "pages": paginated_books.pages,
                    "current_page": paginated_books.page
                },
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error retrieving books: {e}", exc_info=True)
            return error_response("Failed to retrieve books", error=str(e), status_code=500)

    def get_book_by_id(self, book_id):
        # Eager load related entities including the user and location
        book = Book.query.options(

            joinedload(Book.author),
            joinedload(Book.publisher),
            joinedload(Book.user).joinedload(User.location).joinedload(Location.city).joinedload(City.state).joinedload(State.country), # Load user and full location path
            joinedload(Book.categories),
            # Optionally load ratings and the user who made the rating
            # subqueryload(Book.ratings).joinedload(Rating.user)
        ).get(book_id)

        if not book:
            return error_response("Book not found", error="not_found", status_code=404)
        # Use the corrected to_dict method
        # Pass include_ratings=True if you decide to load and include them
        return success_response("Book found", data=book.to_dict(), status_code=200)

    def get_books_by_user(self, owner_user_id, args):
        """Gets books listed by a specific user."""
        # Set the user_id filter in the args and call get_all_books
        args = args.copy() # Avoid modifying the original args dict
        args['user_id'] = owner_user_id
        return self.get_all_books(args)

    def update_book(self, book_id, data, current_user_id):
        # Eager load the user relationship for the authorization check
        book = Book.query.options(joinedload(Book.user)).get(book_id)
        if not book:
            return error_response("Book not found", error="not_found", status_code=404)

        # Authorization Check: Ensure the current user owns the book or is an admin
        user = User.query.get(current_user_id)
        if not user: return error_response("User not found.", error="unauthorized", status_code=401) # Should not happen with jwt_required
        is_owner = book.user_id == current_user_id
        is_admin = user.role == 'admin' # Assuming 'admin' role exists
        if not (is_owner or is_admin):
            logger.warning(f"Unauthorized attempt to update Book ID {book_id} by User ID {current_user_id}")
            return error_response("You are not authorized to update this book.", error="forbidden", status_code=403)

        # Validate Input Data
        errors = validate_book_input(data, is_update=True)
        if errors: return error_response("Validation failed", errors=errors, status_code=400)


        # Fetch and Validate Related Entities (Author, Publisher, Categories)
        related_entities, related_errors = self._get_and_validate_related(data)
        if related_errors:
            errors = (errors or {}) | related_errors
            return error_response("Validation failed", errors=errors, status_code=400)

        # Update fields
        updated = False
        # (Loop through data.items() remains the same)
        for key, value in data.items():
            if key in ['category_ids', 'author_id', 'publisher_id']: continue
            if key == 'price' and value is not None: value = Decimal(str(value))
            # Prevent changing the owner (user_id) via this method
            if key == 'user_id': continue
            if hasattr(book, key) and getattr(book, key) != value:
                setattr(book, key, value)
                updated = True

        # Update relationships (Author, Publisher, Categories)
        if 'author_id' in data:
            new_author = related_entities['author'] if data['author_id'] else None
            if book.author != new_author:
                book.author = new_author
                updated = True
        if 'publisher_id' in data:
            new_publisher = related_entities['publisher'] if data['publisher_id'] else None
            if book.publisher != new_publisher:
                book.publisher = new_publisher
                updated = True
        if 'category_ids' in data:
            # Efficiently update many-to-many: replace current with new set
            current_category_ids = {cat.id for cat in book.categories}
            new_category_ids = set(data.get('category_ids', []))

            if current_category_ids != new_category_ids:
                book.categories = related_entities['categories'] # Assign the list of Category
                updated = True

        if not updated:
            return error_response("No changes detected in the provided data.", error="no_change", status_code=400)


        try:
            # Rating is not updated here; handled by Rating CRUD operations.
            db.session.commit()
            logger.info(f"Book updated: ID {book.id}, Title '{book.title}' by User ID {current_user_id}")
            # Use the corrected to_dict method for the response
            return success_response("Book updated successfully", data=book.to_dict(), status_code=200)
        except IntegrityError as e:
            db.session.rollback()
            logger.error(f"Integrity error updating book {book_id}: {e}", exc_info=True)
            return error_response("Failed to update book due to database constraint.", error="db_integrity_error", status_code=409)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating book {book_id}: {e}", exc_info=True)
            return error_response("Failed to update book", error=str(e), status_code=500)

    def delete_book(self, book_id, current_user_id):
        # Eager load user for authorization check
        book = Book.query.options(joinedload(Book.user)).get(book_id)
        if not book: return error_response("Book not found", error="not_found", status_code=404)

        # Authorization Check
        user = User.query.get(current_user_id)
        if not user: return error_response("User not found.", error="unauthorized", status_code=401)
        is_owner = book.user_id == current_user_id
        is_admin = user.role == 'admin'
        if not (is_owner or is_admin):
            logger.warning(f"Unauthorized attempt to delete Book ID {book_id} by User ID {current_user_id}")
            return error_response("You are not authorized to delete this book.", error="forbidden", status_code=403)

        try:
            book_title = book.title
            # Associated ratings are cascade deleted by DB relationship setting.
            db.session.delete(book)
            db.session.commit()
            logger.info(f"Book deleted: ID {book_id}, Title '{book_title}' by User ID {current_user_id}")

            # Return 204 No Content on successful deletion is common practice
            return success_response("Book deleted successfully", status_code=200) # Or return status_code=204
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting book {book_id}: {e}", exc_info=True)
            return error_response("Failed to delete book", error=str(e), status_code=500)