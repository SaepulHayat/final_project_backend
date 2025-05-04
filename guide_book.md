# Guide: Implementing Book CRUD Operations

This guide details how to implement Create, Read, Update, and Delete (CRUD) operations for the `Book` model, following a layered architecture.

**References:**

- Models: `book.py`, `author.py`, `publisher.py`, `category.py`, `rating.py`, `seller.py`, `user.py`, `book_category_table.py`
- General CRUD Structure (Example): `crud_guide.md` (for Seller)
- Example Implementation Style: `guide_category.md`

## 1. Model Layer (`src/app/model/book.py`)

- **Existing Model:** The `Book` model includes fields like `title`, `description`, `price`, `quantity`, `discount_percent`, image URLs, `rating` (to store the calculated average), and foreign keys (`publisher_id`, `seller_id`, `author_id`).
- **Relationships:**
  - Many-to-One: `publisher`, `author`, `seller`
  - Many-to-Many: `categories` (via `book_category_table`)
  - One-to-Many: `ratings` (with `cascade="all, delete-orphan"`)
- **Responsibilities:** Defines the data structure, relationships, and database mapping for books.
- **Serialization:** Add `to_dict()` for detailed views and `to_simple_dict()` for lists. These now use the stored `rating` field.

  ```python
  # Inside Book class in book.py

  # Note: calculate_average_rating method removed from model.
  # The Book.rating field (Numeric(3, 2)) will be updated by the BookService.

  def to_dict(self, include_ratings=False):
      data = {
          'id': self.id,
          'title': self.title,
          'description': self.description,
          # Use the stored average rating field
          'average_rating': float(self.rating) if self.rating is not None else None,
          'quantity': self.quantity,
          'price': float(self.price) if self.price is not None else None,
          'discount_percent': self.discount_percent,
          'final_price': float(self.price * (1 - self.discount_percent / 100)) if self.price is not None else None,
          'image_url_1': self.image_url_1,
          'image_url_2': self.image_url_2,
          'image_url_3': self.image_url_3,
          'created_at': self.created_at.isoformat() if self.created_at else None,
          'updated_at': self.updated_at.isoformat() if self.updated_at else None,
          # Include simplified related data (assuming simple dict methods exist)
          'author': self.author.to_simple_dict() if self.author else None,
          'publisher': self.publisher.to_simple_dict() if self.publisher else None,
          'seller': self.seller.to_simple_dict() if self.seller else None, # Assuming Seller model has to_simple_dict
          'categories': [category.to_simple_dict() for category in self.categories] if self.categories else [],
          'rating_count': len(self.ratings) # Count of individual ratings
      }
      # Optionally include full rating details
      if include_ratings:
           # Assuming Rating model has to_dict
          data['ratings'] = [rating.to_dict() for rating in self.ratings]
      return data

  def to_simple_dict(self):
      # A lighter version for lists, using the stored rating
      return {
          'id': self.id,
          'title': self.title,
          'average_rating': float(self.rating) if self.rating is not None else None,
          'price': float(self.price) if self.price is not None else None,
          'discount_percent': self.discount_percent,
          'final_price': float(self.price * (1 - self.discount_percent / 100)) if self.price is not None else None,
          'image_url_1': self.image_url_1, # Often include the primary image
          'author_name': f"{self.author.first_name} {self.author.last_name}" if self.author else "N/A",
          'seller_name': self.seller.name if self.seller else "N/A" # Assuming Seller model has name
      }

  # Ensure Author, Publisher, Category, Seller, Rating models also have
  # appropriate to_dict() / to_simple_dict() methods.
  ```

## 2. Utility Layer (`src/app/utils/`)

- **Validators (`validators.py`):**
  - Create `validate_book_input(data, is_update=False)`: (Content remains the same as previous version)
    - **Checks (Create):** `title` (required, string), `price` (required, positive number), `quantity` (required, non-negative integer), `discount_percent` (optional, 0-100 integer), `description` (optional, string), `author_id` (optional, integer - check existence), `publisher_id` (optional, integer - check existence), `category_ids` (optional, list of integers - check existence). `seller_id` is usually derived from the logged-in user, not input data.
    - **Checks (Update):** Similar checks, but fields are optional. If provided, they must meet the constraints.
    - **Existence Checks:** Verify that provided `author_id`, `publisher_id`, and `category_ids` correspond to existing records in their respective tables.
    - Return a dictionary of errors if validation fails, otherwise `None`.
- **Response Formatting (`response.py`):**
  - Use existing `success_response`, `error_response`, `create_response`.
- **Decorators (`decorators.py`):**
  - Use `@jwt_required()` for authenticated endpoints (Create, Update, Delete, Get My Books).
  - Implement or use a role/permission checking decorator (e.g., `@roles_required` or custom logic).

## 3. Service Layer (`src/app/services/book_service.py`)

- **Create `BookService` Class:**

  ```python
  from decimal import Decimal, ROUND_HALF_UP # For price validation and rating rounding
  from flask_jwt_extended import get_jwt_identity # To get current user ID
  from sqlalchemy import func # For average calculation
  from sqlalchemy.orm import joinedload, subqueryload # For eager loading
  from sqlalchemy.exc import IntegrityError
  from ..extensions import db
  from ..model.book import Book
  from ..model.author import Author
  from ..model.publisher import Publisher
  from ..model.category import Category
  from ..model.seller import Seller
  from ..model.user import User # To get seller from user
  from ..model.rating import Rating # Needed for average calculation
  from ..utils.validators import validate_book_input
  from ..utils.response import success_response, error_response
  import logging

  logger = logging.getLogger(__name__)

  class BookService:

      def _get_and_validate_related(self, data):
          """Helper to fetch and validate related entities."""
          # (Content remains the same as previous version)
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
                  if len(categories) != len(set(category_ids)): # Check if all provided IDs were found
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
          for this book is created, updated, or deleted.
          """
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
              # Round to 2 decimal places (matches Book.rating Numeric(3, 2))
              rounded_avg_score = avg_score_decimal.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

              book.rating = rounded_avg_score # Update the book's rating field
              # No commit here - it's handled by the calling function's transaction
              logger.info(f"Updated average rating for Book ID {book_id} to {book.rating}")
          except Exception as e:
              # Log the error but don't let it break the main operation if possible
              logger.error(f"Error updating average rating for Book ID {book_id}: {e}", exc_info=True)
              # Depending on requirements, you might want to re-raise or handle differently
              # Do NOT rollback here, let the calling function handle transaction management.

      def create_book(self, data, user_id):
          # (Steps 1-5 remain the same as previous version)
          # 1. Get Seller Profile
          user = User.query.get(user_id)
          if not user or not user.seller_profile:
               return error_response("Seller profile not found for the current user.", error="forbidden", status_code=403)
          seller = user.seller_profile

          # 2. Validate Input Data
          errors = validate_book_input(data)
          if errors:
              return error_response("Validation failed", errors=errors, status_code=400)

          # 3. Fetch and Validate Related Entities
          related_entities, related_errors = self._get_and_validate_related(data)
          if related_errors:
               errors = (errors or {}) | related_errors
               return error_response("Validation failed", errors=errors, status_code=400)

          # 4. Create Book Instance (Initialize rating to None or 0)
          new_book = Book(
              title=data['title'],
              description=data.get('description'),
              quantity=data['quantity'],
              price=Decimal(str(data['price'])),
              discount_percent=data.get('discount_percent', 0),
              image_url_1=data.get('image_url_1'),
              image_url_2=data.get('image_url_2'),
              image_url_3=data.get('image_url_3'),
              seller=seller,
              author=related_entities['author'],
              publisher=related_entities['publisher'],
              rating=None # Initialize rating - will be updated if ratings are added later
          )

          # 5. Add Categories
          if related_entities['categories']:
              new_book.categories.extend(related_entities['categories'])

          # 6. Add to Session and Commit
          try:
              db.session.add(new_book)
              # Note: Average rating is not updated here as no ratings exist yet.
              # It will be updated when the first rating is added.
              db.session.commit()
              logger.info(f"Book created: ID {new_book.id}, Title '{new_book.title}', Seller ID {seller.id}")
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
          # (Content remains the same, uses Book.rating for sorting if specified)
          page = args.get('page', 1, type=int)
          per_page = args.get('per_page', 12, type=int)
          search_term = args.get('search')
          author_id = args.get('author_id', type=int)
          publisher_id = args.get('publisher_id', type=int)
          category_id = args.get('category_id', type=int)
          seller_id = args.get('seller_id', type=int)
          min_price = args.get('min_price', type=float)
          max_price = args.get('max_price', type=float)
          sort_by = args.get('sort_by', 'created_at')
          order = args.get('order', 'desc')

          query = Book.query.options(
              joinedload(Book.author),
              joinedload(Book.publisher),
              joinedload(Book.seller),
              subqueryload(Book.categories)
          )

          # Filtering (same as before)
          if search_term: query = query.filter(Book.title.ilike(f'%{search_term}%'))
          if author_id: query = query.filter(Book.author_id == author_id)
          if publisher_id: query = query.filter(Book.publisher_id == publisher_id)
          if category_id: query = query.filter(Book.categories.any(Category.id == category_id))
          if seller_id: query = query.filter(Book.seller_id == seller_id)
          if min_price is not None: query = query.filter(Book.price >= Decimal(str(min_price)))
          if max_price is not None: query = query.filter(Book.price <= Decimal(str(max_price)))

          # Sorting
          order_direction = db.desc if order.lower() == 'desc' else db.asc
          if sort_by == 'price':
              query = query.order_by(order_direction(Book.price))
          elif sort_by == 'title':
              query = query.order_by(order_direction(Book.title))
          elif sort_by == 'rating': # Sort by the stored rating field
             query = query.order_by(order_direction(Book.rating))
          else: # Default sort by creation date
              query = query.order_by(order_direction(Book.created_at))

          try:
              paginated_books = query.paginate(page=page, per_page=per_page, error_out=False)
              return success_response(
                  "Books retrieved successfully",
                  data={
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
          # (Content remains the same, uses stored rating in to_dict)
           book = Book.query.options(
              joinedload(Book.author),
              joinedload(Book.publisher),
              joinedload(Book.seller),
              joinedload(Book.categories),
              # subqueryload(Book.ratings).joinedload(Rating.user) # Optionally load ratings
          ).get(book_id)

           if not book:
               return error_response("Book not found", error="not_found", status_code=404)
           return success_response("Book found", data=book.to_dict(include_ratings=True), status_code=200)

      def get_books_by_seller(self, seller_id, args):
           # (Content remains the same)
           args['seller_id'] = seller_id
           return self.get_all_books(args)

      def update_book(self, book_id, data, user_id):
          # (Content remains mostly the same, no rating update needed here unless rating itself is directly editable, which is unlikely)
          book = Book.query.options(joinedload(Book.seller)).get(book_id)
          if not book:
              return error_response("Book not found", error="not_found", status_code=404)

          # Authorization Check
          user = User.query.get(user_id)
          if not user: return error_response("User not found.", error="unauthorized", status_code=401)
          is_owner = book.seller and book.seller.user_id == user_id
          is_admin = user.role == 'admin'
          if not (is_owner or is_admin):
              return error_response("You are not authorized to update this book.", error="forbidden", status_code=403)

          # Validate Input Data
          errors = validate_book_input(data, is_update=True)
          if errors: return error_response("Validation failed", errors=errors, status_code=400)

          # Fetch and Validate Related Entities
          related_entities, related_errors = self._get_and_validate_related(data)
          if related_errors:
               errors = (errors or {}) | related_errors
               return error_response("Validation failed", errors=errors, status_code=400)

          # Update fields
          updated = False
          # (Loop through data.items() remains the same as previous version)
          for key, value in data.items():
              if key in ['category_ids', 'author_id', 'publisher_id']: continue # Handled below/separately
              if key == 'price' and value is not None: value = Decimal(str(value))
              if hasattr(book, key) and getattr(book, key) != value:
                  setattr(book, key, value)
                  updated = True

          # Update relationships (Author, Publisher, Categories) - same logic as before
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
              book.categories.clear()
              if related_entities['categories']:
                  book.categories.extend(related_entities['categories'])
              updated = True

          if not updated:
              return error_response("No changes detected in the provided data.", error="no_change", status_code=400)

          try:
              # Note: Average rating is not updated here. It's updated via Rating CRUD operations.
              db.session.commit()
              logger.info(f"Book updated: ID {book.id}, Title '{book.title}' by User ID {user_id}")
              return success_response("Book updated successfully", data=book.to_dict(), status_code=200)
          except IntegrityError as e:
              db.session.rollback()
              logger.error(f"Integrity error updating book {book_id}: {e}", exc_info=True)
              return error_response("Failed to update book due to database constraint.", error="db_integrity_error", status_code=409)
          except Exception as e:
              db.session.rollback()
              logger.error(f"Error updating book {book_id}: {e}", exc_info=True)
              return error_response("Failed to update book", error=str(e), status_code=500)

      def delete_book(self, book_id, user_id):
          # (Content remains the same)
          book = Book.query.options(joinedload(Book.seller)).get(book_id)
          if not book: return error_response("Book not found", error="not_found", status_code=404)

          # Authorization Check
          user = User.query.get(user_id)
          if not user: return error_response("User not found.", error="unauthorized", status_code=401)
          is_owner = book.seller and book.seller.user_id == user_id
          is_admin = user.role == 'admin'
          if not (is_owner or is_admin):
              return error_response("You are not authorized to delete this book.", error="forbidden", status_code=403)

          try:
              book_title = book.title
              # Associated ratings are cascade deleted by DB relationship setting.
              # No need to call _update_book_average_rating as the book is gone.
              db.session.delete(book)
              db.session.commit()
              logger.info(f"Book deleted: ID {book_id}, Title '{book_title}' by User ID {user_id}")
              return success_response("Book deleted successfully", status_code=200)
          except Exception as e:
              db.session.rollback()
              logger.error(f"Error deleting book {book_id}: {e}", exc_info=True)
              return error_response("Failed to delete book", error=str(e), status_code=500)

  ```

## 4. Route Layer (`src/app/routes/book_route.py`)

- **Create Blueprint and Import Services/Utils:**

  - (Content remains the same as the previous version - routes call the service methods which now incorporate the updated rating logic indirectly).

  ```python
  from flask import Blueprint, request, jsonify
  from flask_jwt_extended import jwt_required, get_jwt_identity
  from ..services.book_service import BookService
  from ..utils.response import create_response
  from ..utils.decorators import roles_required # Assuming roles_required exists
  from ..utils.roles import UserRoles # Assuming UserRoles enum exists
  import logging

  logger = logging.getLogger(__name__)
  book_bp = Blueprint('books', __name__, url_prefix='/api/v1/books')
  book_service = BookService()

  @book_bp.route('/', methods=['POST'])
  @jwt_required()
  # @roles_required(UserRoles.SELLER)
  def create_book_route():
      user_id = get_jwt_identity()
      from ..model.user import User # Temp import
      user = User.query.get(user_id)
      if not user or not user.seller_profile:
           return create_response(status="error", message="Only sellers can create books.", error="forbidden"), 403

      data = request.get_json()
      if not data: return create_response(status="error", message="Request body must be JSON"), 400
      result = book_service.create_book(data, user_id)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @book_bp.route('/', methods=['GET'])
  def get_books_route():
      args = request.args
      result = book_service.get_all_books(args)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @book_bp.route('/<int:book_id>', methods=['GET'])
  def get_book_by_id_route(book_id):
      result = book_service.get_book_by_id(book_id)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @book_bp.route('/me', methods=['GET'])
  @jwt_required()
  # @roles_required(UserRoles.SELLER)
  def get_my_books_route():
      user_id = get_jwt_identity()
      from ..model.user import User # Temp import
      user = User.query.get(user_id)
      if not user or not user.seller_profile:
           return create_response(status="error", message="Seller profile not found.", error="forbidden"), 403
      seller_id = user.seller_profile.id
      args = request.args
      result = book_service.get_books_by_seller(seller_id, args)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @book_bp.route('/<int:book_id>', methods=['PATCH', 'PUT'])
  @jwt_required()
  def update_book_route(book_id):
      user_id = get_jwt_identity()
      data = request.get_json()
      if not data: return create_response(status="error", message="Request body must be JSON"), 400
      result = book_service.update_book(book_id, data, user_id)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @book_bp.route('/<int:book_id>', methods=['DELETE'])
  @jwt_required()
  def delete_book_route(book_id):
      user_id = get_jwt_identity()
      result = book_service.delete_book(book_id, user_id)
      status_code = result.get('status_code', 500)
      if result.get('status') == 'success' and status_code == 200:
          return '', 204
      return create_response(**result), status_code

  # Register blueprint in app factory
  # from .routes.book_route import book_bp
  # app.register_blueprint(book_bp)
  ```

## 5. Key Considerations & Error Handling

- **Role-Based Access Control (RBAC):** (Content remains the same)
- **Input Validation:** (Content remains the same)
- **Relationship Management:** (Content remains the same)
- **Average Rating (`Book.rating`):**
  - The `Book.rating` field (type `Numeric(3, 2)`) is now used to **store** the calculated average rating.
  - The calculation and update logic resides in the `BookService._update_book_average_rating(book_id)` helper function.
  - **Crucially, `_update_book_average_rating` must be called by the service layer logic responsible for managing `Rating` entities (e.g., a hypothetical `RatingService`) immediately after a `Rating` associated with the book is successfully created, updated, or deleted.** This ensures the `Book.rating` field stays synchronized. The call should happen within the same database transaction as the rating change.
  - The `to_dict` and `to_simple_dict` methods now read directly from `self.rating`.
  - Sorting by rating in `get_all_books` now uses the stored `Book.rating` column.
- **Error Handling Strategy:** (Content remains the same)
- **Pagination & Filtering:** (Content remains the same)
- **Serialization (`to_dict`, `to_simple_dict`):** (Content remains the same, but now reads stored rating)

This updated guide reflects the strategy of calculating the average rating in the service layer and storing it in the `Book.rating` field, making the model simpler and centralizing the update logic. Remember to implement the calls to `_update_book_average_rating` in the appropriate places within your `Rating` management logic.
