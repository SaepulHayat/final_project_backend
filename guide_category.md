# Guide: Implementing Category CRUD Operations

This guide details how to implement Create, Read, Update, and Delete (CRUD) operations for the Category model, adhering to a layered architecture similar to the one used for Authors. [cite: 1]

**Reference:** [cite: 2]

- Category Model: `category.py` [cite: 2]
- Book Model (for relationship): `book.py` [cite: 2]
- CRUD Plan: `crud_plan_3.md` [cite: 2]

## 1. Model Layer (`src/app/model/category.py`)

- **Existing Model:** The Category model uses `id`, `name` (required, unique), `created_at`, `updated_at`. [cite: 2]
- **Relationship:** It has a many-to-many relationship with the Book model (`books = db.relationship('Book', secondary=book_category_table, back_populates='categories')`). [cite: 3]
- **Responsibilities:** Defines the data structure and database mapping for categories. [cite: 4]
- **Serialization:** Implement `to_dict()` and `to_simple_dict()` methods to control API output: [cite: 5]

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
          # Add if needed, being mindful of performance. [cite: 6]
      }
      return data # Added return statement for completeness [cite: 6]

  def to_simple_dict(self, include_books=False): # For data retrieval (getting)
      """Returns a simple dictionary representation of the category."""
      data = {
          'id': self.id,
          'name': self.name
      }
      if include_books:
          # Assumes Book model has a to_simple_dict() method
          data['books'] = [book.to_simple_dict() for book in self.books] # [cite: 7]
      return data
  ```

## 2. Utility Layer (`src/app/utils/`)

- **Validators (`validators.py`):**
  - Create a validation function: `validate_category_input(data, is_update=False)`
  - Checks:
    - `name` is present (unless `is_update` is True and `name` is not provided). [cite: 8]
    - `name` is non-empty and within reasonable length constraints (e.g., `db.String(100)`). [cite: 8]
  - Return a dictionary of errors if validation fails, otherwise `None`. [cite: 8]
- **Response Formatting (`response.py`):**
  - Utilize the existing `success_response`, `error_response`, and `create_response` functions for consistent API responses. [cite: 9]
- **Decorators (`decorators.py`):**
  - Use `@jwt_required()` for endpoints requiring authentication (Create, Update, Delete). [cite: 10]
  - Implement or use a role-checking decorator (e.g., `@roles_required(UserRoles.ADMIN)`) to enforce permissions. [cite: 10] Based on `crud_plan_3.md`, reading categories might be public, while CUD operations likely require Admin privileges. [cite: 11]

## 3. Service Layer (`src/app/services/category_service.py`) [cite: 12]

- **Create Category Service Class:** [cite: 12]

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
          if errors: # [cite: 13]
              return error_response("Validation failed", errors=errors, status_code=400) # [cite: 13]

          # Strip whitespace and apply title case [cite: 13]
          name_input = data.get('name', "").strip() # [cite: 13]
          if not name_input: # Re-check after stripping if name was just whitespace [cite: 13]
              return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400) # [cite: 13]
          name = name_input.title() # Capitalize first letter of each word [cite: 13]

          # Check for name uniqueness (case-insensitive comparison) [cite: 13]
          existing_category = Category.query.filter(func.lower(Category.name) == func.lower(name)).first() # [cite: 13]
          if existing_category: # [cite: 13]
              # Return conflict even if casing is different, as we store title-cased [cite: 13]
              return error_response(f"Category '{name}' already exists", error="duplicate_name", status_code=409) # 409 Conflict [cite: 13]

          new_category = Category(name=name) # Store the title-cased name [cite: 13]
          try: # [cite: 13]
              db.session.add(new_category) # [cite: 13]
              db.session.commit() # [cite: 13]
              logger.info(f"Category created: ID {new_category.id}, Name '{new_category.name}'") # [cite: 13]
              # Use the to_dict() method from the model for the response data [cite: 14]
              return success_response("Category created successfully", data=new_category.to_dict(), status_code=201) # [cite: 14]
          except IntegrityError as e: # Catch potential race condition duplicate [cite: 14]
              db.session.rollback() # [cite: 14]
              logger.warning(f"Integrity error creating category '{name}': {e}") # [cite: 14]
              return error_response(f"Category '{name}' already exists", error="duplicate_name", status_code=409) # [cite: 14]
          except Exception as e: # [cite: 14]
              db.session.rollback() # [cite: 14]
              logger.error(f"Error creating category '{name}': {e}", exc_info=True) # [cite: 14]
              return error_response("Failed to create category", error=str(e), status_code=500) # [cite: 14]

      def get_all_categories(self, args):
          # Implement pagination, filtering (e.g., by name), searching [cite: 14]
          page = args.get('page', 1, type=int) # [cite: 14]
          per_page = args.get('per_page', 10, type=int) # [cite: 14]
          search_term = args.get('search') # [cite: 15]
          query = Category.query.order_by(Category.name) # Order alphabetically [cite: 15]

          if search_term: # [cite: 15]
              query = query.filter(Category.name.ilike(f'%{search_term}%')) # [cite: 15]

          try: # [cite: 15]
              paginated_categories = query.paginate(page=page, per_page=per_page, error_out=False) # [cite: 15]
              return success_response( # [cite: 15]
                  "Categories retrieved successfully", # [cite: 15]
                  data={ # [cite: 15]
                      # Use the to_dict() method from the model for each category [cite: 15]
                      "categories": [cat.to_dict() for cat in paginated_categories.items], # [cite: 15]
                      "total": paginated_categories.total, # [cite: 15]
                      "pages": paginated_categories.pages, # [cite: 15]
                      "current_page": paginated_categories.page # [cite: 15]
                  }, # [cite: 15]
                  status_code=200 # [cite: 15]
              ) # [cite: 15]
          except Exception as e: # [cite: 15]
              logger.error(f"Error retrieving categories: {e}", exc_info=True) # [cite: 15]
              return error_response("Failed to retrieve categories", error=str(e), status_code=500) # [cite: 15]

      def get_category_by_id(self, category_id):
          category = Category.query.get(category_id) # [cite: 15]
          if not category: # [cite: 15]
              return error_response("Category not found", error="not_found", status_code=404) # [cite: 15]
          # Use the to_dict() method from the model for the response data [cite: 15]
          return success_response("Category found", data=category.to_dict(), status_code=200) # [cite: 15]

      def get_books_by_category(self, category_id, args):
          category = Category.query.get(category_id) # [cite: 15]
          if not category: # [cite: 15]
              return error_response("Category not found", error="not_found", status_code=404) # [cite: 15]

          # Implement pagination for books within the category [cite: 15]
          page = args.get('page', 1, type=int) # [cite: 15]
          per_page = args.get('per_page', 10, type=int) # [cite: 15]

          try: # [cite: 16]
              # Access books through the relationship and paginate [cite: 16]
              # Ensure Book model has a to_simple_dict() method [cite: 16]
              paginated_books = Book.query.with_parent(category).paginate(page=page, per_page=per_page, error_out=False) # [cite: 16]
              return success_response( # [cite: 16]
                  f"Books in category '{category.name}' retrieved successfully", # [cite: 16]
                  data={ # [cite: 16]
                      # Use Book's to_simple_dict() [cite: 16]
                      "books": [book.to_simple_dict() for book in paginated_books.items], # [cite: 16]
                      "total": paginated_books.total, # [cite: 16]
                      "pages": paginated_books.pages, # [cite: 16]
                      "current_page": paginated_books.page, # [cite: 16]
                      # Use Category's to_simple_dict() (without books) [cite: 16]
                      "category": category.to_simple_dict() # [cite: 16]
                  }, # [cite: 16]
                  status_code=200 # [cite: 16]
              ) # [cite: 16]
          except Exception as e: # [cite: 16]
              logger.error(f"Error retrieving books for category {category_id}: {e}", exc_info=True) # [cite: 16]
              return error_response("Failed to retrieve books for category", error=str(e), status_code=500) # [cite: 16]

      def update_category(self, category_id, data):
          category = Category.query.get(category_id) # [cite: 16]
          if not category: # [cite: 16]
              return error_response("Category not found", error="not_found", status_code=404) # [cite: 16]

          errors = validate_category_input(data, is_update=True) # Allow partial updates [cite: 16]
          if errors: # [cite: 16]
              return error_response("Validation failed", errors=errors, status_code=400) # [cite: 16]

          updated = False # [cite: 16]
          new_name_title_cased = None # Variable to hold the potential new name [cite: 16]
          if 'name' in data: # [cite: 16]
              name_input = data['name'].strip() # [cite: 17]
              if not name_input: # Check if name is empty after stripping [cite: 17]
                  return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400) # [cite: 18]

              new_name_title_cased = name_input.title() # Apply title case [cite: 18]

              # Check if name actually changed (case-insensitive comparison with original) [cite: 18]
              # and also compare title-cased new name with current name [cite: 18]
              if new_name_title_cased.lower() != category.name.lower(): # [cite: 18]
                  # Check if the *new* title-cased name already exists (excluding the current category) [cite: 18]
                  existing_category = Category.query.filter( # [cite: 18]
                      func.lower(Category.name) == func.lower(new_name_title_cased), # [cite: 18]
                      Category.id != category_id # [cite: 18]
                  ).first() # [cite: 18]
                  if existing_category: # [cite: 18]
                      return error_response(f"Another category with the name '{new_name_title_cased}' already exists", error="duplicate_name", status_code=409) # [cite: 18]
                  category.name = new_name_title_cased # Update with title-cased name [cite: 18]
                  updated = True # [cite: 18]
              elif new_name_title_cased != category.name: # [cite: 18]
                  # Handles case where only casing changes e.g. "sci fi" -> "Sci Fi" but lower is same [cite: 18]
                  category.name = new_name_title_cased # [cite: 18]
                  updated = True # [cite: 18]

          if not updated: # [cite: 18]
              # If name was provided but resulted in no change (same name, same case) [cite: 19]
              if 'name' in data: # [cite: 19]
                  return error_response("Provided name is the same as the current name", error="no_change", status_code=400) # [cite: 19]
              else: # [cite: 19]
                  # If 'name' was not in data dictionary at all [cite: 19]
                  return error_response("No update data provided", error="no_change", status_code=400) # [cite: 19]

          try: # [cite: 19]
              db.session.commit() # [cite: 19]
              logger.info(f"Category updated: ID {category.id}, New Name '{category.name}'") # [cite: 19]
              # Use the to_dict() method from the model for the response data [cite: 19]
              return success_response("Category updated successfully", data=category.to_dict(), status_code=200) # [cite: 19]
          except IntegrityError as e: # Catch potential race condition duplicate [cite: 20]
              db.session.rollback() # [cite: 20]
              logger.warning(f"Integrity error updating category {category_id} to '{new_name_title_cased}': {e}") # [cite: 20]
              # Use the name variable that caused the error [cite: 20]
              return error_response(f"Another category with the name '{new_name_title_cased}' already exists", error="duplicate_name", status_code=409) # [cite: 20]
          except Exception as e: # [cite: 20]
              db.session.rollback() # [cite: 20]
              logger.error(f"Error updating category {category_id}: {e}", exc_info=True) # [cite: 20]
              return error_response("Failed to update category", error=str(e), status_code=500) # [cite: 20]

      def delete_category(self, category_id):
          category = Category.query.get(category_id) # [cite: 20]
          if not category: # [cite: 20]
              return error_response("Category not found", error="not_found", status_code=404) # [cite: 20]

          # **Relationship Handling:** For many-to-many, deleting the category [cite: 20]
          # should automatically remove associations from the join table [cite: 20]
          # ('book_category_table') due to how SQLAlchemy handles relationships, [cite: 20]
          # *without* deleting the books themselves. No explicit check is needed [cite: 21]
          # to prevent deletion based on associated books, unlike a one-to-many. [cite: 21]

          try: # [cite: 22]
              category_name = category.name # Store name for logging before deletion [cite: 22]
              db.session.delete(category) # [cite: 22]
              db.session.commit() # [cite: 22]
              logger.info(f"Category deleted: ID {category_id}, Name '{category_name}'") # [cite: 22]
              # Return 204 No Content status code via the route handler [cite: 22]
              return success_response("Category deleted successfully", status_code=200) # Route will change to 204 [cite: 22]
          except Exception as e: # Catch potential DB errors [cite: 22]
              db.session.rollback() # [cite: 22]
              logger.error(f"Error deleting category {category_id}: {e}", exc_info=True) # [cite: 22]
              return error_response("Failed to delete category", error=str(e), status_code=500) # [cite: 22]

  # Responsibilities: Encapsulates all business logic related to categories, interacts with [cite: 22]
  # the database via the Category model, performs validation (including uniqueness [cite: 22]
  # checks), handles relationships (implicitly for deletion in M2M), and manages specific [cite: 22]
  # errors. [cite: 23]
  ```

## 4. Route Layer (`src/app/routes/category_route.py`) [cite: 23]

- **Create Blueprint and Import Services/Utils:** [cite: 23]

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
      args = request.args # For pagination/filtering/searching [cite: 24]
      result = category_service.get_all_categories(args) # [cite: 24]
      status_code = result.get('status_code', 500) # [cite: 24]
      return create_response(**result), status_code # [cite: 24]

  @category_bp.route('/<int:category_id>', methods=['GET'])
  # Public endpoint
  def get_category_by_id_route(category_id): # [cite: 25]
      result = category_service.get_category_by_id(category_id) # [cite: 25]
      status_code = result.get('status_code', 500) # [cite: 25]
      return create_response(**result), status_code # [cite: 25]

  @category_bp.route('/<int:category_id>/books', methods=['GET'])
  # Public endpoint
  def get_books_by_category_route(category_id):
      args = request.args # For pagination [cite: 25]
      result = category_service.get_books_by_category(category_id, args) # [cite: 25]
      status_code = result.get('status_code', 500) # [cite: 25]
      return create_response(**result), status_code # [cite: 25]

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
      if result.get('status') == 'success' and status_code == 200: # [cite: 25]
          return "", 204 # Return empty body with 204 status [cite: 25]
      return create_response(**result), status_code # [cite: 26]

  # Register blueprint in app factory (e.g., in app/__init__.py) [cite: 26]
  # from .routes.category_route import category_bp [cite: 26]
  # app.register_blueprint(category_bp) [cite: 26]

  # Responsibilities: Defines API endpoints, handles HTTP request/response cycle, parses [cite: 26]
  # request data (JSON body, query args), calls the CategoryService, applies security [cite: 27]
  # decorators (@jwt_required, @roles_required), and uses create_response to format the [cite: 27]
  # final JSON output with appropriate HTTP status codes. [cite: 27]
  ```

## 5. Key Considerations & Error Handling [cite: 28]

- **Role-Based Access Control (RBAC):** [cite: 28]
  - **Public Read:** Listing categories (`/`) and getting a specific category (`/<id>`) and its books (`/<id>/books`) should generally be public. [cite: 28]
  - **Admin CUD:** Creating, updating, and deleting categories should typically be restricted to Admin users via `@roles_required(UserRoles.ADMIN)`. [cite: 29]
- **Input Validation:** [cite: 30]
  - Performed in `CategoryService` via `validate_category_input`. [cite: 30]
  - Ensures `name` is present, non-empty, and meets length requirements. [cite: 30]
  - Returns 400 Bad Request for validation errors. [cite: 31]
- **Name Formatting:** [cite: 31]
  - Category names are automatically converted to title case (e.g., "historical fiction" becomes "Historical Fiction") before being saved during creation and updates. [cite: 31]
- **Uniqueness Constraint:** [cite: 32]
  - The `name` field has a unique constraint in the database (`UniqueConstraint('name', name='uq_category_name')`). [cite: 32]
  - The `create_category` and `update_category` service methods include explicit, case-insensitive checks before attempting the database operation to provide a clearer error message (409 Conflict). [cite: 33] The check compares against the title-cased version of the input name. [cite: 34]
  - `IntegrityError` is caught during commit as a fallback for race conditions. [cite: 35]
- **Error Handling Strategy:** [cite: 36]
  - **Service Layer:** Returns dictionaries containing status, message, data (on success), error (code/key), errors (validation details), and `status_code`. [cite: 36] This makes the service layer responsible for determining the appropriate HTTP status. [cite: 37]
  - **Route Layer:** Unpacks the dictionary returned by the service into `create_response`. [cite: 38] Uses the `status_code` from the service response. [cite: 38] Handles basic request errors (e.g., missing JSON body). [cite: 39] Implements the 204 No Content response for successful deletions. [cite: 39]
- **Relationship Management (Deletion):** [cite: 40]
  - Deleting a Category with a many-to-many relationship (like books) managed by SQLAlchemy will automatically remove the corresponding entries from the association table (`book_category_table`). [cite: 40]
  - It will NOT delete the associated Book objects. [cite: 41] This is the desired behavior - removing a category just means books no longer belong to it. [cite: 41]
  - No special check is needed in `delete_category` to prevent deletion based on associated books. [cite: 42]
- **Pagination & Filtering:** [cite: 43]
  - Implement in `get_all_categories` and `get_books_by_category` service methods using SQLAlchemy's `paginate()` and filtering (`.filter()`, `.ilike()`). [cite: 43]
  - Accept query parameters (`page`, `per_page`, `search`) in the corresponding route functions (`request.args`). [cite: 44]
- **Serialization (`to_dict()` / `to_simple_dict()`):** [cite: 45]
  - The `to_dict()` and `to_simple_dict()` methods on the Category model control the API response structure for categories. [cite: 45]
  - Ensure related models (like Book) also have appropriate serialization methods (`to_simple_dict()` is used in the service layer examples for books). [cite: 46]

By following these steps, you can implement robust and maintainable CRUD operations for the Category model, consistent with the application's overall architecture and the specific requirements outlined in `crud_plan_3.md`. [cite: 47]
