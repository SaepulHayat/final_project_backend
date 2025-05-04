# Guide: Implementing Rating CRUD Operations

This guide details how to implement Create, Read, Update, and Delete (CRUD) operations for the `Rating` model, adhering to a layered architecture and incorporating logic for relationships and access control.

**Reference:**

- Rating Model: `rating.py`
- User Model: `user.py`
- Book Model: `book.py`
- CRUD Plan: `crud_guide.md`

## 1. Model Layer (`src/app/model/rating.py`)

- **Existing Model:** The `Rating` model includes `id`, `user_id` (FK to `users`), `book_id` (FK to `book`), `score` (integer 1-5), `text` (optional), `created_at`, `updated_at`.

- **Relationships:**

  - **Rating to User (Many-to-One):** Each rating is associated with exactly one user (`User`) who wrote it. This is defined by the `user_id` foreign key. From a `Rating` object, you can access the associated user via `rating.user`. Conversely (due to `back_populates`), from a `User` object, you can access all their ratings via `user.ratings`.
  - **Rating to Book (Many-to-One):** Each rating is associated with exactly one book (`Book`) that it reviews. This is defined by the `book_id` foreign key. From a `Rating` object, you can access the associated book via `rating.book`. Conversely, from a `Book` object, you can access all its ratings via `book.ratings`.

  ```python
  # Inside Rating class in rating.py
  user = db.relationship('User', back_populates='ratings')
  book = db.relationship('Book', back_populates='ratings')

  # Corresponding relationship in User class (user.py - implied by back_populates)
  # ratings = db.relationship('Rating', back_populates='user', lazy='dynamic') # Example

  # Corresponding relationship in Book class (book.py)
  # ratings = db.relationship('Rating', back_populates='book', cascade='all, delete-orphan')
  ```

- **Responsibilities:** Defines the data structure and database mapping for ratings.

- **Serialization:** Add a `to_dict()` method to control API output. Include basic user and book information for context.

  ```python
  # Inside Rating class in rating.py
  def to_dict(self, include_user=True, include_book=True):
      data = {
          'id': self.id,
          'user_id': self.user_id,
          'book_id': self.book_id,
          'score': self.score,
          'text': self.text,
          'created_at': self.created_at.isoformat() if self.created_at else None,
          'updated_at': self.updated_at.isoformat() if self.updated_at else None
      }
      # Optionally include simplified related object info
      # Assumes User and Book models have a to_simple_dict() or similar
      if include_user and self.user:
           # Example: Use user's simple dict or just specific fields
          data['user'] = {
              'id': self.user.id,
              'full_name': self.user.full_name
          }
          # Or: data['user'] = self.user.to_simple_dict()
      if include_book and self.book:
           # Example: Use book's simple dict or just specific fields
          data['book'] = {
              'id': self.book.id,
              'title': self.book.title
          }
          # Or: data['book'] = self.book.to_simple_dict()
      return data

  # Consider adding a to_simple_dict if needed elsewhere
  def to_simple_dict(self):
       return {
          'id': self.id,
          'score': self.score,
          'user_id': self.user_id # Keep user_id for potential filtering
       }
  ```

## 2. Utility Layer (`src/app/utils/`)

- **Validators (`validators.py`):**
  - Create `validate_rating_input(data, is_update=False)`:
    - Checks:
      - `score` is present (unless `is_update` and not provided).
      - `score` is an integer.
      - `score` is between 1 and 5 (inclusive).
      - `text` (if present) is a string and within reasonable length limits (e.g., 1000 characters).
    - Return a dictionary of errors if validation fails, otherwise `None`.
- **Response Formatting (`response.py`):**
  - Utilize the existing `success_response`, `error_response`, and `create_response` functions.
- **Decorators (`decorators.py`):**
  - Use `@jwt_required()` for endpoints requiring authentication (Create, Read Own, Update, Delete).
  - Use or implement a role-checking decorator (e.g., `@roles_required(...)`) based on `crud_guide.md`. Note that specific ownership checks (User/Seller can only modify their _own_ ratings) will often need to be handled within the service or route logic in addition to role checks.
- **Roles (`roles.py`):**
  - Assume an enum `UserRoles` exists (e.g., `UserRoles.USER`, `UserRoles.SELLER`, `UserRoles.ADMIN`).

## 3. Service Layer (`src/app/services/rating_service.py`)

- **Create `RatingService` Class:**

  ```python
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
                      "ratings": [r.to_dict(include_book=False) for r in paginated_ratings.items], # Don't need book info again
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
                      "ratings": [r.to_dict(include_user=False) for r in paginated_ratings.items], # Don't need user info again
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

  ```

- **Responsibilities:** Encapsulates business logic for ratings: validation, checking book existence, preventing duplicate ratings per user/book, checking ownership for updates/deletes, calculating and updating the average book rating (`Book.rating`), interacting with the database, and handling errors.

## 4. Route Layer (`src/app/routes/rating_route.py`)

- **Create Blueprints and Import Services/Utils:** Routes might be split or nested.

  - A blueprint nested under books: `/api/v1/books/<int:book_id>/ratings` (POST, GET list)
  - A blueprint nested under users: `/api/v1/users/` (GET `/me/ratings`, GET `/<int:user_id>/ratings` for Admin)
  - A top-level blueprint: `/api/v1/ratings/<int:rating_id>` (GET specific, PATCH, DELETE)

  ```python
  from flask import Blueprint, request, jsonify
  from flask_jwt_extended import jwt_required, get_jwt_identity # To get current user ID
  from ..services.rating_service import RatingService
  from ..utils.response import create_response
  from ..utils.decorators import roles_required # Assuming roles_required exists
  from ..utils.roles import UserRoles # Assuming UserRoles enum exists
  from ..model.user import User # To get user role
  import logging

  logger = logging.getLogger(__name__)

  # --- Blueprint for /books/{book_id}/ratings ---
  book_ratings_bp = Blueprint('book_ratings', __name__, url_prefix='/api/v1/books/<int:book_id>/ratings')
  rating_service = RatingService() # Instantiate service

  @book_ratings_bp.route('/', methods=['POST'])
  @jwt_required()
  # roles_required(UserRoles.USER, UserRoles.SELLER) # Users and Sellers can rate
  def create_rating_route(book_id):
      user_identity = get_jwt_identity() # Get user info from JWT (e.g., user_id)
      user_id = user_identity.get('id') if isinstance(user_identity, dict) else user_identity # Adjust based on JWT content
      # Optional: Check user role if needed, though service handles logic like duplicates
      # user = User.query.get(user_id)
      # if user.role not in [UserRoles.USER.value, UserRoles.SELLER.value]:
      #      return create_response(status="error", message="Forbidden"), 403

      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      result = rating_service.create_rating(book_id, user_id, data)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @book_ratings_bp.route('/', methods=['GET'])
  # Public endpoint - No @jwt_required needed
  def get_ratings_for_book_route(book_id):
      args = request.args # For pagination/sorting
      result = rating_service.get_ratings_for_book(book_id, args)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  # --- Blueprint for /users/.../ratings ---
  user_ratings_bp = Blueprint('user_ratings', __name__, url_prefix='/api/v1/users')

  @user_ratings_bp.route('/me/ratings', methods=['GET'])
  @jwt_required()
  # roles_required(UserRoles.USER, UserRoles.SELLER, UserRoles.ADMIN) # All authenticated users can see their own
  def get_my_ratings_route():
      user_identity = get_jwt_identity()
      user_id = user_identity.get('id') if isinstance(user_identity, dict) else user_identity
      args = request.args
      result = rating_service.get_ratings_by_user(user_id, args)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @user_ratings_bp.route('/<int:user_id>/ratings', methods=['GET'])
  @jwt_required()
  @roles_required(UserRoles.ADMIN) # Only Admins can view others' ratings by user ID
  def get_user_ratings_route(user_id):
      args = request.args
      result = rating_service.get_ratings_by_user(user_id, args)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  # --- Blueprint for /ratings/{rating_id} ---
  ratings_bp = Blueprint('ratings', __name__, url_prefix='/api/v1/ratings')

  @ratings_bp.route('/<int:rating_id>', methods=['GET'])
  @jwt_required(optional=True) # Allow anonymous access if needed, or make required
  def get_rating_by_id_route(rating_id):
      # According to plan, only Admin can get arbitrary rating ID directly.
      # User/Seller view their own via /users/me/ratings.
      # Let's enforce Admin-only for this specific endpoint.
      # If public access is needed, remove/adjust roles_required.
      # This requires roles_required to be applied *conditionally* or handled inside.
      # Simpler approach: Make it Admin only via decorator.
      # @roles_required(UserRoles.ADMIN) # Uncomment if strictly Admin only

      # Alternative: Check role inside if decorator not flexible enough
      user_identity = get_jwt_identity()
      current_user_id = None
      current_user_role = None
      if user_identity:
           current_user_id = user_identity.get('id') if isinstance(user_identity, dict) else user_identity
           # Fetch role based on ID - requires User model access
           user = User.query.get(current_user_id)
           if user:
               current_user_role = UserRoles(user.role) # Convert string role to enum

      # If only Admin can access this endpoint:
      if not current_user_role or current_user_role != UserRoles.ADMIN:
           # Check if the user is trying to access their own rating (if allowed by plan)
           # rating = Rating.query.get(rating_id) # Need to fetch rating first
           # if not rating or rating.user_id != current_user_id:
           #      return create_response(status="error", message="Forbidden"), 403
           # For now, assume only Admin as per plan's note on this specific endpoint
           return create_response(status="error", message="Forbidden: Admin access required"), 403


      result = rating_service.get_rating_by_id(rating_id) # Pass user info if service needs it for checks
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code


  @ratings_bp.route('/<int:rating_id>', methods=['PATCH'])
  @jwt_required()
  # No specific role needed here, service layer handles ownership/admin check
  def update_rating_route(rating_id):
      user_identity = get_jwt_identity()
      current_user_id = user_identity.get('id') if isinstance(user_identity, dict) else user_identity
      # Fetch user role to pass to service for authorization check
      user = User.query.get(current_user_id)
      if not user:
           return create_response(status="error", message="User not found"), 404 # Should not happen if JWT is valid
      current_user_role = UserRoles(user.role)

      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      result = rating_service.update_rating(rating_id, current_user_id, current_user_role, data)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @ratings_bp.route('/<int:rating_id>', methods=['DELETE'])
  @jwt_required()
  # No specific role needed here, service layer handles ownership/admin check
  def delete_rating_route(rating_id):
      user_identity = get_jwt_identity()
      current_user_id = user_identity.get('id') if isinstance(user_identity, dict) else user_identity
      # Fetch user role to pass to service for authorization check
      user = User.query.get(current_user_id)
      if not user:
           return create_response(status="error", message="User not found"), 404
      current_user_role = UserRoles(user.role)

      result = rating_service.delete_rating(rating_id, current_user_id, current_user_role)
      status_code = result.get('status_code', 500)

      # Return 204 No Content on successful deletion
      if result.get('status') == 'success' and status_code == 200:
          return '', 204
      return create_response(**result), status_code

  # Register blueprints in app factory (e.g., in app/__init__.py)
  # from .routes.rating_route import book_ratings_bp, user_ratings_bp, ratings_bp
  # app.register_blueprint(book_ratings_bp)
  # app.register_blueprint(user_ratings_bp)
  # app.register_blueprint(ratings_bp)

  ```

- **Responsibilities:** Defines API endpoints according to the plan, handles HTTP requests/responses, parses data, extracts user identity from JWT, applies security decorators (`@jwt_required`, `@roles_required`), calls the `RatingService`, performs necessary authorization checks (especially fetching the user's role for service layer checks), and formats the final JSON output using `create_response`.

## 5. Key Considerations & Error Handling

- **Role-Based Access Control (RBAC) & Ownership:**
  - **Create:** Requires authentication (`@jwt_required`), allowed for Users and Sellers.
  - **Read (List):** `/books/{book_id}/ratings` is public. `/users/me/ratings` requires authentication. `/users/{user_id}/ratings` requires Admin role (`@roles_required(UserRoles.ADMIN)`).
  - **Read (Specific):** `/ratings/{rating_id}` requires Admin role according to the plan notes (or potentially owner access - clarify requirement).
  - **Update/Delete:** `/ratings/{rating_id}` requires authentication. The **service layer** must check if the `current_user.id` matches `rating.user_id` OR if `current_user.role` is Admin. Route layer fetches the current user's role and passes it to the service.
- **Input Validation:**
  - Performed in `RatingService` via `validate_rating_input`.
  - Ensures `score` is a required integer between 1-5. `text` is optional.
  - Returns 400 Bad Request for validation errors.
- **Duplicate Rating Prevention:**
  - The `create_rating` service method explicitly checks if the user has already rated the specific book before creating a new rating.
  - Returns 409 Conflict if a duplicate is found.
- **Average Book Rating (`Book.rating`):**
  - This is a critical side-effect handled by the `_update_book_average_rating` helper method within the `RatingService`.
  - It **must** be called after successful `create_rating`, `update_rating`, and `delete_rating` operations _before_ the final commit (or just after flush for delete).
  - Uses `func.avg` and `Decimal` for accurate calculation and rounding. Handles cases where a book might have zero ratings.
- **Error Handling Strategy:**
  - **Service Layer:** Returns dictionaries with `status`, `message`, `data`, `error`, `errors`, and `status_code`.
  - **Route Layer:** Unpacks the service response dictionary into `create_response`. Uses the `status_code` from the service. Handles basic request errors and converts successful DELETE responses to 204 No Content.
- **Pagination & Sorting:**
  - Implement in `get_ratings_for_book` and `get_ratings_by_user` service methods using SQLAlchemy's `paginate()` and ordering.
  - Accept query parameters (`page`, `per_page`, `sort_by`, `sort_order`) in the route functions (`request.args`).
- **Serialization (`to_dict()`):**
  - The `Rating.to_dict()` method controls the API output structure. Include simplified nested data for `user` and `book` where appropriate (e.g., when listing ratings for a book, you already know the book, so `include_book=False`).

By following this guide, you can implement the CRUD operations for the Rating model, ensuring data integrity, proper authorization, and automatic updates to related models like the average book rating.
