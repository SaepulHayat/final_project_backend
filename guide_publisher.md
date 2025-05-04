# Guide: Implementing Publisher CRUD Operations

This guide details how to implement Create, Read, Update, and Delete (CRUD) operations for the `Publisher` model, adhering to a layered architecture.

**Reference:**

- Publisher Model: `publisher.py`
- Book Model (for relationship): `book.py`
- CRUD Plan: `crud_guide.md`

## 1. Model Layer (`src/app/model/publisher.py`)

- **Existing Model:** The `Publisher` model uses `id`, `name` (required, unique), `created_at`, `updated_at`.
- **Relationship:** It has a one-to-many relationship with the `Book` model (`books = db.relationship('Book', back_populates='publisher')`). The `Book` model has a `publisher_id` foreign key which is `nullable=True`.
- **Responsibilities:** Defines the data structure and database mapping for publishers.
- **Serialization:** Add `to_dict()` and `to_simple_dict()` methods to control API output:

  ```python
  # Inside Publisher class in publisher.py
  def to_dict(self, include_books=False):
      data = {
          'id': self.id,
          'name': self.name,
          'created_at': self.created_at.isoformat() if self.created_at else None,
          'updated_at': self.updated_at.isoformat() if self.updated_at else None,
          # Consider adding book count carefully for performance
          # 'book_count': len(self.books) # This can be inefficient
      }
      # Optionally include simplified book info - use with caution on list endpoints
      if include_books:
           data['books'] = [book.to_simple_dict() for book in self.books]
      return data

  # Simpler version for lists or embedding in other objects
  def to_simple_dict(self):
       return {
           'id': self.id,
           'name': self.name
       }

  # Add corresponding methods to Book model if not present
  # Inside Book class in book.py
  # def to_simple_dict(self):
  #     return {
  #         'id': self.id,
  #         'title': self.title
  #         # Add other simple fields as needed
  #     }
  ```

## 2. Utility Layer (`src/app/utils/`)

- **Validators (`validators.py`):**
  - Create a validation function: `validate_publisher_input(data, is_update=False)`
    - Checks:
      - `name` is present (unless `is_update` is True and `name` is not provided).
      - `name` is a non-empty string after stripping whitespace.
      - `name` is within reasonable length constraints (e.g., matching `db.String(255)`).
    - Return a dictionary of errors if validation fails, otherwise `None`.
- **Response Formatting (`response.py`):**
  - Utilize the existing `success_response`, `error_response`, and `create_response` functions for consistent API responses.
- **Decorators (`decorators.py`):**
  - Use `@jwt_required()` for endpoints requiring authentication (Create, Update, Delete).
  - Implement or use a role-checking decorator (e.g., `@roles_required()`) to enforce permissions based on `crud_guide.md`:
    - Create: `Admin`, `Seller`
    - Update: `Admin`
    - Delete: `Admin`
    - Read (All, One, Books): Public (no role check needed, but potentially `@jwt_required(optional=True)` if user-specific data might be added later).

## 3. Service Layer (`src/app/services/publisher_service.py`)

- **Create `PublisherService` Class:**

  ```python
  from ..model.publisher import Publisher
  from ..model.book import Book # Needed for querying books by publisher and handling deletion
  from ..extensions import db
  from ..utils.validators import validate_publisher_input
  from ..utils.response import success_response, error_response # Or handle errors via exceptions
  from sqlalchemy import func # For case-insensitive checks
  from sqlalchemy.exc import IntegrityError # To catch unique constraint violations
  import logging

  logger = logging.getLogger(__name__)

  class PublisherService:
      def create_publisher(self, data):
          errors = validate_publisher_input(data)
          if errors:
              return error_response("Validation failed", errors=errors, status_code=400)

          name_input = data.get('name', '').strip()
          if not name_input: # Re-check after stripping
               return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)

          # Check for name uniqueness (case-insensitive comparison)
          existing_publisher = Publisher.query.filter(func.lower(Publisher.name) == func.lower(name_input)).first()
          if existing_publisher:
              return error_response(f"Publisher '{name_input}' already exists", error="duplicate_name", status_code=409) # 409 Conflict

          new_publisher = Publisher(name=name_input) # Store the name as provided (trimmed)
          try:
              db.session.add(new_publisher)
              db.session.commit()
              logger.info(f"Publisher created: ID {new_publisher.id}, Name '{new_publisher.name}'")
              return success_response("Publisher created successfully", data=new_publisher.to_dict(), status_code=201)
          except IntegrityError as e: # Catch potential race condition duplicate
              db.session.rollback()
              logger.warning(f"Integrity error creating publisher '{name_input}': {e}")
              return error_response(f"Publisher '{name_input}' already exists", error="duplicate_name", status_code=409)
          except Exception as e:
              db.session.rollback()
              logger.error(f"Error creating publisher '{name_input}': {e}", exc_info=True)
              return error_response("Failed to create publisher", error=str(e), status_code=500)

      def get_all_publishers(self, args):
          # Implement pagination, filtering (e.g., by name), searching
          page = args.get('page', 1, type=int)
          per_page = args.get('per_page', 10, type=int)
          search_term = args.get('search')

          query = Publisher.query.order_by(Publisher.name) # Order alphabetically
          if search_term:
              query = query.filter(Publisher.name.ilike(f'%{search_term}%'))

          try:
              paginated_publishers = query.paginate(page=page, per_page=per_page, error_out=False)
              return success_response(
                  "Publishers retrieved successfully",
                  data={
                      # Use simple dict for lists
                      "publishers": [pub.to_simple_dict() for pub in paginated_publishers.items],
                      "total": paginated_publishers.total,
                      "pages": paginated_publishers.pages,
                      "current_page": paginated_publishers.page
                  },
                  status_code=200
              )
          except Exception as e:
              logger.error(f"Error retrieving publishers: {e}", exc_info=True)
              return error_response("Failed to retrieve publishers", error=str(e), status_code=500)

      def get_publisher_by_id(self, publisher_id):
          publisher = Publisher.query.get(publisher_id)
          if not publisher:
              return error_response("Publisher not found", error="not_found", status_code=404)
          # Use full dict for single item view
          return success_response("Publisher found", data=publisher.to_dict(), status_code=200)

      def get_books_by_publisher(self, publisher_id, args):
          publisher = Publisher.query.get(publisher_id)
          if not publisher:
              return error_response("Publisher not found", error="not_found", status_code=404)

          # Implement pagination for books within the publisher
          page = args.get('page', 1, type=int)
          per_page = args.get('per_page', 10, type=int)

          try:
              # Access books through the relationship and paginate
              # Ensure Book model has a to_simple_dict() method
              paginated_books = Book.query.with_parent(publisher).paginate(page=page, per_page=per_page, error_out=False)

              return success_response(
                  f"Books by publisher '{publisher.name}' retrieved successfully",
                  data={
                      "books": [book.to_simple_dict() for book in paginated_books.items], # Use simple book representation
                      "total": paginated_books.total,
                      "pages": paginated_books.pages,
                      "current_page": paginated_books.page,
                      "publisher": publisher.to_simple_dict() # Include publisher info
                  },
                  status_code=200
              )
          except Exception as e:
               logger.error(f"Error retrieving books for publisher {publisher_id}: {e}", exc_info=True)
               return error_response("Failed to retrieve books for publisher", error=str(e), status_code=500)


      def update_publisher(self, publisher_id, data):
          publisher = Publisher.query.get(publisher_id)
          if not publisher:
              return error_response("Publisher not found", error="not_found", status_code=404)

          errors = validate_publisher_input(data, is_update=True) # Allow partial updates
          if errors:
              return error_response("Validation failed", errors=errors, status_code=400)

          updated = False
          new_name_input = None
          if 'name' in data:
              name_input = data['name'].strip()
              if not name_input: # Check if name is empty after stripping
                  return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)

              new_name_input = name_input # Keep track of the proposed new name

              # Check if name actually changed (case-insensitive comparison with original)
              if new_name_input.lower() != publisher.name.lower():
                  # Check if the *new* name already exists (excluding the current publisher)
                  existing_publisher = Publisher.query.filter(
                      func.lower(Publisher.name) == func.lower(new_name_input),
                      Publisher.id != publisher_id
                  ).first()
                  if existing_publisher:
                      return error_response(f"Another publisher with the name '{new_name_input}' already exists", error="duplicate_name", status_code=409)

                  publisher.name = new_name_input # Update with new name
                  updated = True
              elif new_name_input != publisher.name:
                   # Handles case where only casing changes but lower is same, still update
                  publisher.name = new_name_input
                  updated = True


          if not updated:
               # If name was provided but resulted in no change
               if 'name' in data:
                   return error_response("Provided name is the same as the current name", error="no_change", status_code=400)
               else:
                   # If 'name' was not in data dictionary at all
                   return error_response("No update data provided", error="no_change", status_code=400)


          try:
              db.session.commit()
              logger.info(f"Publisher updated: ID {publisher.id}, New Name '{publisher.name}'")
              return success_response("Publisher updated successfully", data=publisher.to_dict(), status_code=200)
          except IntegrityError as e: # Catch potential race condition duplicate
              db.session.rollback()
              logger.warning(f"Integrity error updating publisher {publisher_id} to '{new_name_input}': {e}")
              # Use the name variable that caused the error
              return error_response(f"Another publisher with the name '{new_name_input}' already exists", error="duplicate_name", status_code=409)
          except Exception as e:
              db.session.rollback()
              logger.error(f"Error updating publisher {publisher_id}: {e}", exc_info=True)
              return error_response("Failed to update publisher", error=str(e), status_code=500)

      def delete_publisher(self, publisher_id):
          publisher = Publisher.query.get(publisher_id)
          if not publisher:
              return error_response("Publisher not found", error="not_found", status_code=404)

          # **Relationship Handling (One-to-Many with Nullable FK):**
          # Before deleting the publisher, set the `publisher_id` to NULL
          # for all associated books. This prevents foreign key constraint errors
          # and aligns with the nullable FK design.
          try:
              # Efficiently update associated books in bulk
              Book.query.filter(Book.publisher_id == publisher_id).update(
                  {Book.publisher_id: None},
                  synchronize_session=False # Use 'fetch' or False depending on needs/version
              )
              # synchronize_session='fetch' might be needed in some cases to update
              # the session state, but 'False' is often sufficient and faster here.

              publisher_name = publisher.name # Store name for logging before deletion
              db.session.delete(publisher)
              db.session.commit()
              logger.info(f"Publisher deleted: ID {publisher_id}, Name '{publisher_name}'. Associated books' publisher_id set to NULL.")
              # Return success, route will handle 204 No Content
              return success_response("Publisher deleted successfully", status_code=200)
          except Exception as e: # Catch potential DB errors during update or delete
              db.session.rollback()
              logger.error(f"Error deleting publisher {publisher_id} or updating books: {e}", exc_info=True)
              return error_response("Failed to delete publisher", error=str(e), status_code=500)

  ```

- **Responsibilities:** Encapsulates all business logic related to publishers, interacts with the database via the `Publisher` and `Book` models, performs validation (including uniqueness checks), handles relationships (setting `Book.publisher_id` to NULL on delete), and manages specific errors.

## 4. Route Layer (`src/app/routes/publisher_route.py`)

- **Create Blueprint and Import Services/Utils:**

  ```python
  from flask import Blueprint, request, jsonify
  from ..services.publisher_service import PublisherService
  from ..utils.response import create_response # Use create_response to handle service responses
  from ..utils.decorators import jwt_required, roles_required # Assuming roles_required exists
  from ..utils.roles import UserRoles # Assuming UserRoles enum exists
  import logging

  logger = logging.getLogger(__name__)
  publisher_bp = Blueprint('publishers', __name__, url_prefix='/api/v1/publishers')
  publisher_service = PublisherService()

  @publisher_bp.route('/', methods=['POST'])
  @jwt_required()
  @roles_required(UserRoles.ADMIN, UserRoles.SELLER) # Admins or Sellers can create
  def create_publisher_route():
      # Consider adding check: If user is Seller, maybe restrict fields? (Future enhancement)
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      result = publisher_service.create_publisher(data)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @publisher_bp.route('/', methods=['GET'])
  # Public endpoint - no @jwt_required or @roles_required
  def get_publishers_route():
      args = request.args # For pagination/filtering/searching
      result = publisher_service.get_all_publishers(args)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @publisher_bp.route('/<int:publisher_id>', methods=['GET'])
  # Public endpoint
  def get_publisher_by_id_route(publisher_id):
      result = publisher_service.get_publisher_by_id(publisher_id)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @publisher_bp.route('/<int:publisher_id>/books', methods=['GET'])
  # Public endpoint
  def get_books_by_publisher_route(publisher_id):
      args = request.args # For pagination
      result = publisher_service.get_books_by_publisher(publisher_id, args)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @publisher_bp.route('/<int:publisher_id>', methods=['PATCH', 'PUT']) # Allow PUT for full replacement semantics if desired
  @jwt_required()
  @roles_required(UserRoles.ADMIN) # Only Admins can update
  def update_publisher_route(publisher_id):
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      result = publisher_service.update_publisher(publisher_id, data)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @publisher_bp.route('/<int:publisher_id>', methods=['DELETE'])
  @jwt_required()
  @roles_required(UserRoles.ADMIN) # Only Admins can delete
  def delete_publisher_route(publisher_id):
      result = publisher_service.delete_publisher(publisher_id)
      status_code = result.get('status_code', 500)
      # For successful deletion, standard practice is 204 No Content
      if result.get('status') == 'success' and status_code == 200:
          return '', 204 # Return empty body with 204 status
      return create_response(**result), status_code

  # Register blueprint in app factory (e.g., in app/__init__.py)
  # from .routes.publisher_route import publisher_bp
  # app.register_blueprint(publisher_bp)
  ```

- **Responsibilities:** Defines API endpoints according to `crud_guide.md`, handles HTTP request/response cycle, parses request data, calls the `PublisherService`, applies security decorators (`@jwt_required`, `@roles_required`), and uses `create_response` to format the final JSON output with appropriate HTTP status codes.

## 5. Key Considerations & Error Handling

- **Role-Based Access Control (RBAC):**
  - **Public Read:** Listing publishers (`/`), getting a specific publisher (`/<id>`), and listing their books (`/<id>/books`) are public.
  - **Create:** Allowed for `Admin` and `Seller` roles.
  - **Update/Delete:** Restricted to `Admin` users.
- **Input Validation:**
  - Performed in `PublisherService` via `validate_publisher_input`.
  - Ensures `name` is present (on create), non-empty, and meets length requirements.
  - Returns 400 Bad Request for validation errors.
- **Name Formatting:**
  - Publisher names are stored as provided after trimming leading/trailing whitespace. No automatic case conversion is applied (unlike the Category example).
- **Uniqueness Constraint:**
  - The `name` field has a unique constraint (`uq_publisher_name`).
  - The `create_publisher` and `update_publisher` service methods include explicit, case-insensitive checks before the database operation to provide a 409 Conflict error.
  - `IntegrityError` is caught during commit as a fallback.
- **Error Handling Strategy:**
  - **Service Layer:** Returns dictionaries containing `status`, `message`, `data` (on success), `error` (code/key), `errors` (validation details), and `status_code`.
  - **Route Layer:** Unpacks the service response using `create_response`. Handles basic request errors and implements the 204 No Content response for successful deletions.
- **Relationship Management (Deletion):**
  - Deleting a `Publisher` requires handling the one-to-many relationship with `Book`.
  - Since `Book.publisher_id` is **nullable**, the recommended approach (implemented in `delete_publisher`) is to **set `publisher_id` to `None`** for all associated books before deleting the publisher. This prevents data loss (books aren't deleted) and avoids foreign key constraint violations.
  - An alternative (not implemented here) would be to prevent deletion if any books are associated with the publisher, but setting to NULL is generally preferred for nullable foreign keys.
- **Pagination & Filtering:**
  - Implement in `get_all_publishers` and `get_books_by_publisher` service methods using SQLAlchemy's `paginate()` and filtering.
  - Accept query parameters (`page`, `per_page`, `search`) in the routes.
- **Serialization (`to_dict()`):**
  - Implement `to_dict()` and `to_simple_dict()` on the `Publisher` model. Ensure related models (`Book`) also have appropriate serialization methods (`to_simple_dict()` used in the example). Be cautious about including related collections directly in list endpoints due to potential performance issues (N+1 queries).

By following these steps, you can implement robust CRUD operations for the Publisher model, consistent with the application's architecture and the requirements from `crud_guide.md`.
