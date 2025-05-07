# Guide: Implementing Category CRUD Operations

This guide details how to implement Create, Read, Update, and Delete (CRUD) operations for the Category model, adhering to a layered architecture similar to the one used for Authors.

**Reference:**

- Category Model: `category.py`
- Book Model (for relationship): `book.py`

## 1. Model Layer (`src/app/model/category.py`)

- **Existing Model:** The Category model uses `id`, `name` (required, unique), `created_at`, `updated_at`.
- **Relationship:** It has a many-to-many relationship with the Book model (`books = db.relationship('Book', secondary=book_category_table, back_populates='categories')`).
- **Responsibilities:** Defines the data structure and database mapping for categories.
- **Serialization:** Implement `to_dict()` and `to_simple_dict()` methods to control API output:

  ```python
  # Inside Category class in category.py

  def to_dict(self): # For data creation (adding)
      """Returns a detailed dictionary representation of the category."""
      data = {
          'id': self.id,
          'name': self.name,
          'created_at': self.created_at.isoformat() if self.created_at else None,
          'updated_at': self.updated_at.isoformat() if self.updated_at else None,
          # Note: The guide previously suggested adding 'book_count' here,
          # but it's not in the current model implementation.
          # Add if needed, being mindful of performance.
      }
      return data # Added return statement for completeness

  def to_simple_dict(self, include_books=False): # For data retrieval (getting)
      """Returns a simple dictionary representation of the category."""
      data = {
          'id': self.id,
          'name': self.name
      }
      if include_books:
          # Assumes Book model has a to_simple_dict() method
          data['books'] = [book.to_simple_dict() for book in self.books] #
      return data
  ```

## 2. Utility Layer (`src/app/utils/`)

- **Validators (`validators.py`):**
  - Create a validation function: `validate_category_input(data, is_update=False)`
  - Checks:
    - `name` is present (unless `is_update` is True and `name` is not provided).
    - `name` is non-empty and within reasonable length constraints (e.g., `db.String(100)`).
  - Return a dictionary of errors if validation fails, otherwise `None`.
- **Response Formatting (`response.py`):**
  - Utilize the existing `success_response`, `error_response`, and `create_response` functions for consistent API responses.
- **Decorators (`decorators.py`):**
  - Use `@jwt_required()` for endpoints requiring authentication (Create, Update, Delete).
  - Implement or use a role-checking decorator (e.g., `@roles_required(UserRoles.ADMIN)`) to enforce permissions. Based on `crud_plan_3.md`, reading categories might be public, while CUD operations likely require Admin privileges.

## 3. Service Layer (`src/app/services/category_service.py`)

- **Create Category Service Class:**

  ```python
  from ..model.category import Category
  from ..model.book import Book # Needed for querying books by category
  from ..extensions import db
  from ..utils.validators import validate_category_input
  from ..utils.response import success_response, error_response # Or handle errors via exceptions
  from sqlalchemy import func # For case-insensitive checks
  from sqlalchemy.exc import IntegrityError # To catch unique constraint violations
  import logging

  logger = logging.getLogger(__name__)

  class CategoryService:

      def create_category(self, data):
          errors = validate_category_input(data)
          if errors: #
              return error_response("Validation failed", errors=errors, status_code=400) #

          # Strip whitespace and apply title case
          name_input = data.get('name', "").strip() #
          if not name_input: # Re-check after stripping if name was just whitespace
              return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400) #
          name = name_input.title() # Capitalize first letter of each word

          # Check for name uniqueness (case-insensitive comparison)
          existing_category = Category.query.filter(func.lower(Category.name) == func.lower(name)).first() #
          if existing_category: #
              # Return conflict even if casing is different, as we store title-cased
              return error_response(f"Category '{name}' already exists", error="duplicate_name", status_code=409) # 409 Conflict

          new_category = Category(name=name) # Store the title-cased name
          try: #
              db.session.add(new_category) #
              db.session.commit() #
              logger.info(f"Category created: ID {new_category.id}, Name '{new_category.name}'") #
              # Use the to_dict() method from the model for the response data
              return success_response("Category created successfully", data=new_category.to_dict(), status_code=201) #
          except IntegrityError as e: # Catch potential race condition duplicate
              db.session.rollback() #
              logger.warning(f"Integrity error creating category '{name}': {e}") #
              return error_response(f"Category '{name}' already exists", error="duplicate_name", status_code=409) #
          except Exception as e: #
              db.session.rollback() #
              logger.error(f"Error creating category '{name}': {e}", exc_info=True) #
              return error_response("Failed to create category", error=str(e), status_code=500) #

      def get_all_categories(self, args):
          # Implement pagination, filtering (e.g., by name), searching
          page = args.get('page', 1, type=int) #
          per_page = args.get('per_page', 10, type=int) #
          search_term = args.get('search') #
          query = Category.query.order_by(Category.name) # Order alphabetically

          if search_term: #
              query = query.filter(Category.name.ilike(f'%{search_term}%')) #

          try: #
              paginated_categories = query.paginate(page=page, per_page=per_page, error_out=False) #
              return success_response( #
                  "Categories retrieved successfully", #
                  data={ #
                      # Use the to_dict() method from the model for each category
                      "categories": [cat.to_dict() for cat in paginated_categories.items], #
                      "total": paginated_categories.total, #
                      "pages": paginated_categories.pages, #
                      "current_page": paginated_categories.page #
                  }, #
                  status_code=200 #
              ) #
          except Exception as e: #
              logger.error(f"Error retrieving categories: {e}", exc_info=True) #
              return error_response("Failed to retrieve categories", error=str(e), status_code=500) #

      def get_category_by_id(self, category_id):
          category = Category.query.get(category_id) #
          if not category: #
              return error_response("Category not found", error="not_found", status_code=404) #
          # Use the to_dict() method from the model for the response data
          return success_response("Category found", data=category.to_dict(), status_code=200) #

      def get_books_by_category(self, category_id, args):
          category = Category.query.get(category_id) #
          if not category: #
              return error_response("Category not found", error="not_found", status_code=404) #

          # Implement pagination for books within the category
          page = args.get('page', 1, type=int) #
          per_page = args.get('per_page', 10, type=int) #

          try: #
              # Access books through the relationship and paginate
              # Ensure Book model has a to_simple_dict() method
              paginated_books = Book.query.with_parent(category).paginate(page=page, per_page=per_page, error_out=False) #
              return success_response( #
                  f"Books in category '{category.name}' retrieved successfully", #
                  data={ #
                      # Use Book's to_simple_dict()
                      "books": [book.to_simple_dict() for book in paginated_books.items], #
                      "total": paginated_books.total, #
                      "pages": paginated_books.pages, #
                      "current_page": paginated_books.page, #
                      # Use Category's to_simple_dict() (without books)
                      "category": category.to_simple_dict() #
                  }, #
                  status_code=200 #
              ) #
          except Exception as e: #
              logger.error(f"Error retrieving books for category {category_id}: {e}", exc_info=True) #
              return error_response("Failed to retrieve books for category", error=str(e), status_code=500) #

      def update_category(self, category_id, data):
          category = Category.query.get(category_id) #
          if not category: #
              return error_response("Category not found", error="not_found", status_code=404) #

          errors = validate_category_input(data, is_update=True) # Allow partial updates
          if errors: #
              return error_response("Validation failed", errors=errors, status_code=400) #

          updated = False #
          new_name_title_cased = None # Variable to hold the potential new name
          if 'name' in data: #
              name_input = data['name'].strip() #
              if not name_input: # Check if name is empty after stripping
                  return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400) #

              new_name_title_cased = name_input.title() # Apply title case

              # Check if name actually changed (case-insensitive comparison with original)
              # and also compare title-cased new name with current name
              if new_name_title_cased.lower() != category.name.lower(): #
                  # Check if the *new* title-cased name already exists (excluding the current category)
                  existing_category = Category.query.filter( #
                      func.lower(Category.name) == func.lower(new_name_title_cased), #
                      Category.id != category_id #
                  ).first() #
                  if existing_category: #
                      return error_response(f"Another category with the name '{new_name_title_cased}' already exists", error="duplicate_name", status_code=409) #
                  category.name = new_name_title_cased # Update with title-cased name
                  updated = True #
              elif new_name_title_cased != category.name: #
                  # Handles case where only casing changes e.g. "sci fi" -> "Sci Fi" but lower is same
                  category.name = new_name_title_cased #
                  updated = True #

          if not updated: #
              # If name was provided but resulted in no change (same name, same case)
              if 'name' in data: #
                  return error_response("Provided name is the same as the current name", error="no_change", status_code=400) #
              else: #
                  # If 'name' was not in data dictionary at all
                  return error_response("No update data provided", error="no_change", status_code=400) #

          try: #
              db.session.commit() #
              logger.info(f"Category updated: ID {category.id}, New Name '{category.name}'") #
              # Use the to_dict() method from the model for the response data
              return success_response("Category updated successfully", data=category.to_dict(), status_code=200) #
          except IntegrityError as e: # Catch potential race condition duplicate
              db.session.rollback() #
              logger.warning(f"Integrity error updating category {category_id} to '{new_name_title_cased}': {e}") #
              # Use the name variable that caused the error
              return error_response(f"Another category with the name '{new_name_title_cased}' already exists", error="duplicate_name", status_code=409) #
          except Exception as e: #
              db.session.rollback() #
              logger.error(f"Error updating category {category_id}: {e}", exc_info=True) #
              return error_response("Failed to update category", error=str(e), status_code=500) #

      def delete_category(self, category_id):
          category = Category.query.get(category_id) #
          if not category: #
              return error_response("Category not found", error="not_found", status_code=404) #

          # **Relationship Handling:** For many-to-many, deleting the category
          # should automatically remove associations from the join table
          # ('book_category_table') due to how SQLAlchemy handles relationships,
          # *without* deleting the books themselves. No explicit check is needed
          # to prevent deletion based on associated books, unlike a one-to-many.

          try: #
              category_name = category.name # Store name for logging before deletion
              db.session.delete(category) #
              db.session.commit() #
              logger.info(f"Category deleted: ID {category_id}, Name '{category_name}'") #
              # Return 204 No Content status code via the route handler
              return success_response("Category deleted successfully", status_code=200) # Route will change to 204
          except Exception as e: # Catch potential DB errors
              db.session.rollback() #
              logger.error(f"Error deleting category {category_id}: {e}", exc_info=True) #
              return error_response("Failed to delete category", error=str(e), status_code=500) #

  # Responsibilities: Encapsulates all business logic related to categories, interacts with
  # the database via the Category model, performs validation (including uniqueness
  # checks), handles relationships (implicitly for deletion in M2M), and manages specific
  # errors.
  ```

## 4. Route Layer (`src/app/routes/category_route.py`)

- **Create Blueprint and Import Services/Utils:**

  ```python
  from flask import Blueprint, request, jsonify
  from ..services.category_service import CategoryService
  from ..utils.response import create_response # Use create_response to handle service responses
  from ..utils.decorators import jwt_required, roles_required # Assuming roles_required exists
  from ..utils.roles import UserRoles # Assuming UserRoles enum exists
  import logging

  logger = logging.getLogger(__name__)

  category_bp = Blueprint('categories', __name__, url_prefix='/api/v1/categories')
  category_service = CategoryService()

  @category_bp.route('/', methods=['POST'])
  @jwt_required()
  @roles_required(UserRoles.ADMIN) # Only Admins can create categories
  def create_category_route():
      data = request.get_json()
      if not data:
          # Use create_response directly for simple errors
          return create_response(status="error", message="Request body must be JSON"), 400

      result = category_service.create_category(data)
      # Use status_code from service response if available, else default
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @category_bp.route('/', methods=['GET'])
  # Public endpoint - no @jwt_required or @roles_required
  def get_categories_route():
      args = request.args # For pagination/filtering/searching
      result = category_service.get_all_categories(args) #
      status_code = result.get('status_code', 500) #
      return create_response(**result), status_code #

  @category_bp.route('/<int:category_id>', methods=['GET'])
  # Public endpoint
  def get_category_by_id_route(category_id): #
      result = category_service.get_category_by_id(category_id) #
      status_code = result.get('status_code', 500) #
      return create_response(**result), status_code #

  @category_bp.route('/<int:category_id>/books', methods=['GET'])
  # Public endpoint
  def get_books_by_category_route(category_id):
      args = request.args # For pagination
      result = category_service.get_books_by_category(category_id, args) #
      status_code = result.get('status_code', 500) #
      return create_response(**result), status_code #

  @category_bp.route('/<int:category_id>', methods=['PATCH', 'PUT']) # Allow PUT for full replacement semantics if desired
  @jwt_required()
  @roles_required(UserRoles.ADMIN) # Only Admins can update categories
  def update_category_route(category_id):
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      result = category_service.update_category(category_id, data)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @category_bp.route('/<int:category_id>', methods=['DELETE'])
  @jwt_required()
  @roles_required(UserRoles.ADMIN) # Only Admins can delete categories
  def delete_category_route(category_id):
      result = category_service.delete_category(category_id)
      status_code = result.get('status_code', 500)

      # For successful deletion, standard practice is 204 No Content
      if result.get('status') == 'success' and status_code == 200: #
          return "", 204 # Return empty body with 204 status
      return create_response(**result), status_code #

  # Register blueprint in app factory (e.g., in app/__init__.py)
  # from .routes.category_route import category_bp
  # app.register_blueprint(category_bp)

  # Responsibilities: Defines API endpoints, handles HTTP request/response cycle, parses
  # request data (JSON body, query args), calls the CategoryService, applies security
  # decorators (@jwt_required, @roles_required), and uses create_response to format the
  # final JSON output with appropriate HTTP status codes.
  ```

## 5. Key Considerations & Error Handling

- **Role-Based Access Control (RBAC):**
  - **Public Read:** Listing categories (`/`) and getting a specific category (`/<id>`) and its books (`/<id>/books`) should generally be public.
  - **Admin CUD:** Creating, updating, and deleting categories should typically be restricted to Admin users via `@roles_required(UserRoles.ADMIN)`.
- **Input Validation:**
  - Performed in `CategoryService` via `validate_category_input`.
  - Ensures `name` is present, non-empty, and meets length requirements.
  - Returns 400 Bad Request for validation errors.
- **Name Formatting:**
  - Category names are automatically converted to title case (e.g., "historical fiction" becomes "Historical Fiction") before being saved during creation and updates.
- **Uniqueness Constraint:**
  - The `name` field has a unique constraint in the database (`UniqueConstraint('name', name='uq_category_name')`).
  - The `create_category` and `update_category` service methods include explicit, case-insensitive checks before attempting the database operation to provide a clearer error message (409 Conflict). The check compares against the title-cased version of the input name.
  - `IntegrityError` is caught during commit as a fallback for race conditions.
- **Error Handling Strategy:**
  - **Service Layer:** Returns dictionaries containing status, message, data (on success), error (code/key), errors (validation details), and `status_code`. This makes the service layer responsible for determining the appropriate HTTP status.
  - **Route Layer:** Unpacks the dictionary returned by the service into `create_response`. Uses the `status_code` from the service response. Handles basic request errors (e.g., missing JSON body). Implements the 204 No Content response for successful deletions.
- **Relationship Management (Deletion):**
  - Deleting a Category with a many-to-many relationship (like books) managed by SQLAlchemy will automatically remove the corresponding entries from the association table (`book_category_table`).
  - It will NOT delete the associated Book objects. This is the desired behavior - removing a category just means books no longer belong to it.
  - No special check is needed in `delete_category` to prevent deletion based on associated books.
- **Pagination & Filtering:**
  - Implement in `get_all_categories` and `get_books_by_category` service methods using SQLAlchemy's `paginate()` and filtering (`.filter()`, `.ilike()`).
  - Accept query parameters (`page`, `per_page`, `search`) in the corresponding route functions (`request.args`).
- **Serialization (`to_dict()` / `to_simple_dict()`):**
  - The `to_dict()` and `to_simple_dict()` methods on the Category model control the API response structure for categories.
  - Ensure related models (like Book) also have appropriate serialization methods (`to_simple_dict()` is used in the service layer examples for books).

By following these steps, you can implement robust and maintainable CRUD operations for the Category model, consistent with the application's overall architecture and the specific requirements outlined in `crud_plan_3.md`.
