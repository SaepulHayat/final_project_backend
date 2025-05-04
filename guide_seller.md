# Guide: Implementing Seller CRUD Operations

This guide details how to implement Create, Read, Update, and Delete (CRUD) operations for the `Seller` model, adhering to a layered architecture and referencing the provided CRUD plan.

**References:**

- Seller Model: `seller.py`
- Book Model (for relationship): `book.py`
- User Model (for relationship): `user.py` (Assumed structure)
- CRUD Plan: `crud_guide.md`

## 1. Model Layer (`src/app/model/seller.py`)

- **Existing Model:** The `Seller` model includes `id`, `user_id` (required, unique FK to `users.id`), `name` (required), `location` (optional), `created_at`, `updated_at`.
- **Relationships:**
  - One-to-One with `User` (`user = db.relationship('User', back_populates='seller_profile')`).
  - One-to-Many with `Book` (`books = db.relationship('Book', back_populates='seller', cascade="all, delete-orphan")`). The `Book` model has a non-nullable `seller_id` foreign key.
- **Responsibilities:** Defines the data structure and database mapping for sellers.
- **Serialization:** Add `to_dict()` and `to_simple_dict()` methods to control API output:

  ```python
  # Inside Seller class in seller.py
  def to_dict(self, include_books=False, include_user=False):
      data = {
          'id': self.id,
          'user_id': self.user_id,
          'name': self.name,
          'location': self.location,
          'created_at': self.created_at.isoformat() if self.created_at else None,
          'updated_at': self.updated_at.isoformat() if self.updated_at else None,
          # Consider adding book count carefully for performance
          # 'book_count': len(self.books) # Can be inefficient
      }
      # Optionally include simplified user info
      if include_user and self.user:
           # Assumes User model has to_simple_dict()
           data['user'] = self.user.to_simple_dict()
      # Optionally include simplified book info - use with caution on list endpoints
      if include_books:
           # Assumes Book model has to_simple_dict()
           data['books'] = [book.to_simple_dict() for book in self.books]
      return data

  # Simpler version for lists or embedding
  def to_simple_dict(self):
       return {
           'id': self.id,
           'name': self.name,
           'location': self.location # Include location in simple view too
       }

  # --- Ensure corresponding methods exist in related models ---

  # Inside User class in user.py (Example structure)
  # def to_simple_dict(self):
  #     return {
  #         'id': self.id,
  #         'username': self.username, # Or email, etc.
  #         'email': self.email
  #     }

  # Inside Book class in book.py (Example structure)
  # def to_simple_dict(self):
  #     return {
  #         'id': self.id,
  #         'title': self.title,
  #         'price': str(self.price), # Convert Decimal to string for JSON
  #         'image_url_1': self.image_url_1
  #         # Add other simple fields as needed
  #     }
  ```

## 2. Utility Layer (`src/app/utils/`)

- **Validators (`validators.py`):**
  - Create a validation function: `validate_seller_input(data, is_update=False)`
    - Checks:
      - `name`: Present (unless `is_update` is True and `name` is not provided), non-empty string after stripping, within length constraints (e.g., `db.String(150)`).
      - `location`: If present, non-empty string after stripping, within length constraints (e.g., `db.String(255)`).
    - Return a dictionary of errors if validation fails, otherwise `None`.
- **Response Formatting (`response.py`):**
  - Utilize existing `success_response`, `error_response`, and `create_response` functions.
- **Decorators (`decorators.py`):**
  - Use `@jwt_required()` for endpoints requiring authentication.
  - Implement or use a role-checking decorator (e.g., `@roles_required()`) based on `crud_guide.md`. Assume `UserRoles` enum exists (e.g., `UserRoles.USER`, `UserRoles.SELLER`, `UserRoles.ADMIN`).

## 3. Service Layer (`src/app/services/seller_service.py`)

- **Create `SellerService` Class:**

  ```python
  from ..model.seller import Seller
  from ..model.book import Book # Needed for relationship cascade understanding
  from ..model.user import User # Needed for user relationship and potential role update
  from ..extensions import db
  from ..utils.validators import validate_seller_input
  from ..utils.response import success_response, error_response # Or handle via exceptions
  from sqlalchemy.exc import IntegrityError # To catch unique constraint violations
  import logging

  logger = logging.getLogger(__name__)

  class SellerService:
      def create_seller(self, data, current_user_id):
          # Check if user already has a seller profile
          existing_seller = Seller.query.filter_by(user_id=current_user_id).first()
          if existing_seller:
              return error_response(
                  "User already has a seller profile",
                  error="profile_exists",
                  status_code=409 # Conflict
              )

          errors = validate_seller_input(data)
          if errors:
              return error_response("Validation failed", errors=errors, status_code=400)

          name_input = data.get('name', '').strip()
          location_input = data.get('location', '').strip() or None # Store None if empty after strip

          if not name_input: # Re-check after stripping
               return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)

          new_seller = Seller(
              user_id=current_user_id,
              name=name_input,
              location=location_input
          )

          try:
              # **Potential User Role Update Logic:**
              # user = User.query.get(current_user_id)
              # if user and user.role != UserRoles.SELLER: # Assuming role attribute exists
              #     user.role = UserRoles.SELLER # Or add 'Seller' role
              #     db.session.add(user) # Stage user update

              db.session.add(new_seller)
              db.session.commit()
              logger.info(f"Seller profile created for User ID {current_user_id}: Seller ID {new_seller.id}, Name '{new_seller.name}'")
              # Include user info in the response
              return success_response(
                  "Seller profile created successfully",
                  data=new_seller.to_dict(include_user=True), # Include user details
                  status_code=201
              )
          except IntegrityError as e: # Catch potential race condition on user_id unique constraint
              db.session.rollback()
              logger.warning(f"Integrity error creating seller profile for user {current_user_id}: {e}")
              # Check if it's the unique constraint violation
              if 'uq_seller_user_id' in str(e.orig): # Adjust based on actual constraint name
                   return error_response("User already has a seller profile", error="profile_exists", status_code=409)
              else:
                   return error_response("Database error during seller creation", error=str(e), status_code=500)
          except Exception as e:
              db.session.rollback()
              logger.error(f"Error creating seller profile for user {current_user_id}: {e}", exc_info=True)
              return error_response("Failed to create seller profile", error=str(e), status_code=500)

      def get_all_sellers(self, args):
          page = args.get('page', 1, type=int)
          per_page = args.get('per_page', 10, type=int)
          search_term = args.get('search')
          sort_by = args.get('sort_by', 'name') # Default sort by name
          order = args.get('order', 'asc') # Default order ascending

          query = Seller.query

          if search_term:
              # Search by name or location
              search_filter = f'%{search_term}%'
              query = query.filter(
                  db.or_(Seller.name.ilike(search_filter), Seller.location.ilike(search_filter))
              )

          # Sorting logic
          sort_column = getattr(Seller, sort_by, Seller.name) # Default to name if invalid sort_by
          if order.lower() == 'desc':
              query = query.order_by(sort_column.desc())
          else:
              query = query.order_by(sort_column.asc())


          try:
              paginated_sellers = query.paginate(page=page, per_page=per_page, error_out=False)
              return success_response(
                  "Sellers retrieved successfully",
                  data={
                      # Use simple dict for lists
                      "sellers": [seller.to_simple_dict() for seller in paginated_sellers.items],
                      "total": paginated_sellers.total,
                      "pages": paginated_sellers.pages,
                      "current_page": paginated_sellers.page
                  },
                  status_code=200
              )
          except Exception as e:
              logger.error(f"Error retrieving sellers: {e}", exc_info=True)
              return error_response("Failed to retrieve sellers", error=str(e), status_code=500)

      def get_seller_profile(self, current_user_id):
          # Find seller profile linked to the currently authenticated user
          seller = Seller.query.filter_by(user_id=current_user_id).first()
          if not seller:
              return error_response("Seller profile not found for current user", error="not_found", status_code=404)
          # Return full details including user and books for the owner's view
          return success_response(
              "Seller profile found",
              data=seller.to_dict(include_books=True, include_user=True),
              status_code=200
          )

      def get_seller_by_id(self, seller_id):
          # Find any seller by their ID (public view)
          seller = Seller.query.get(seller_id)
          if not seller:
              return error_response("Seller not found", error="not_found", status_code=404)
          # Return public details - potentially include books but not detailed user info
          return success_response(
              "Seller found",
              data=seller.to_dict(include_books=True, include_user=False), # Don't expose user details publicly
              status_code=200
          )

      def update_my_seller_profile(self, current_user_id, data):
          seller = Seller.query.filter_by(user_id=current_user_id).first()
          if not seller:
              return error_response("Seller profile not found for current user", error="not_found", status_code=404)

          errors = validate_seller_input(data, is_update=True) # Allow partial updates
          if errors:
              return error_response("Validation failed", errors=errors, status_code=400)

          updated = False
          if 'name' in data:
              name_input = data['name'].strip()
              if not name_input:
                   return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)
              if name_input != seller.name:
                  seller.name = name_input
                  updated = True
          if 'location' in data:
               # Allow setting location to empty/None
              location_input = data['location'].strip() if data['location'] is not None else None
              if location_input != seller.location:
                  seller.location = location_input
                  updated = True

          if not updated:
              return error_response("No changes detected in provided data", error="no_change", status_code=400)

          try:
              db.session.commit()
              logger.info(f"Seller profile updated for User ID {current_user_id}: Seller ID {seller.id}")
              return success_response(
                  "Seller profile updated successfully",
                  data=seller.to_dict(include_user=True), # Return updated profile with user info
                  status_code=200
              )
          except Exception as e:
              db.session.rollback()
              logger.error(f"Error updating seller profile for user {current_user_id}: {e}", exc_info=True)
              return error_response("Failed to update seller profile", error=str(e), status_code=500)

      def update_seller_by_id(self, seller_id, data):
          # Admin only - update any seller profile
          seller = Seller.query.get(seller_id)
          if not seller:
              return error_response("Seller not found", error="not_found", status_code=404)

          # Reuse the same update logic as 'update_my_seller_profile'
          errors = validate_seller_input(data, is_update=True)
          if errors:
              return error_response("Validation failed", errors=errors, status_code=400)

          updated = False
          if 'name' in data:
              name_input = data['name'].strip()
              if not name_input:
                   return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)
              if name_input != seller.name:
                  seller.name = name_input
                  updated = True
          if 'location' in data:
              location_input = data['location'].strip() if data['location'] is not None else None
              if location_input != seller.location:
                  seller.location = location_input
                  updated = True

          if not updated:
              return error_response("No changes detected in provided data", error="no_change", status_code=400)

          try:
              db.session.commit()
              logger.info(f"Admin updated Seller profile: ID {seller.id}")
              return success_response(
                  "Seller profile updated successfully",
                  data=seller.to_dict(include_user=True), # Include user info for admin context
                  status_code=200
              )
          except Exception as e:
              db.session.rollback()
              logger.error(f"Error updating seller profile {seller_id} by admin: {e}", exc_info=True)
              return error_response("Failed to update seller profile", error=str(e), status_code=500)


      def delete_seller(self, seller_id):
          # Admin only
          seller = Seller.query.get(seller_id)
          if not seller:
              return error_response("Seller not found", error="not_found", status_code=404)

          # **Relationship Handling (Cascade Delete):**
          # The `cascade="all, delete-orphan"` on `Seller.books` means
          # SQLAlchemy will automatically delete all associated `Book` records
          # when the `Seller` is deleted. This is a significant side effect.
          # Consider if associated user role should be reverted here.
          seller_name = seller.name # Store for logging
          user_id = seller.user_id
          try:
              # **Potential User Role Reversion Logic:**
              # user = User.query.get(user_id)
              # if user and user.role == UserRoles.SELLER: # Check current role
              #     user.role = UserRoles.USER # Revert to default role
              #     db.session.add(user)

              db.session.delete(seller)
              db.session.commit()
              logger.info(f"Seller deleted: ID {seller_id}, Name '{seller_name}', User ID {user_id}. Associated books also deleted due to cascade.")
              # Return success, route will handle 204 No Content
              return success_response("Seller profile deleted successfully", status_code=200)
          except Exception as e:
              db.session.rollback()
              logger.error(f"Error deleting seller {seller_id}: {e}", exc_info=True)
              return error_response("Failed to delete seller profile", error=str(e), status_code=500)

  ```

- **Responsibilities:** Encapsulates business logic for sellers, interacts with `Seller`, `Book`, and `User` models, performs validation, handles uniqueness (`user_id`), manages errors, and coordinates relationship effects (cascade delete).

## 4. Route Layer (`src/app/routes/seller_route.py`)

- **Create Blueprint and Import Services/Utils:**

  ```python
  from flask import Blueprint, request, jsonify
  from flask_jwt_extended import jwt_required, get_jwt_identity # To get current user ID
  from ..services.seller_service import SellerService
  from ..utils.response import create_response # Use create_response to handle service responses
  from ..utils.decorators import roles_required # Assuming roles_required exists
  from ..utils.roles import UserRoles # Assuming UserRoles enum exists
  import logging

  logger = logging.getLogger(__name__)
  seller_bp = Blueprint('sellers', __name__, url_prefix='/api/v1/sellers')
  seller_service = SellerService()

  @seller_bp.route('/', methods=['POST'])
  @jwt_required()
  # Any authenticated user can attempt to create a profile (service layer checks uniqueness)
  # @roles_required(UserRoles.USER) # Might be redundant if jwt_required is sufficient
  def create_seller_route():
      current_user_id = get_jwt_identity() # Get user ID from JWT
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      result = seller_service.create_seller(data, current_user_id)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @seller_bp.route('/', methods=['GET'])
  # Public endpoint - no @jwt_required or @roles_required
  def get_sellers_route():
      args = request.args # For pagination/filtering/searching/sorting
      result = seller_service.get_all_sellers(args)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @seller_bp.route('/me', methods=['GET'])
  @jwt_required()
  @roles_required(UserRoles.SELLER, UserRoles.ADMIN) # Only Sellers or Admins can view their own profile via /me
  def get_my_seller_profile_route():
      current_user_id = get_jwt_identity()
      result = seller_service.get_seller_profile(current_user_id)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @seller_bp.route('/<int:seller_id>', methods=['GET'])
  # Public endpoint
  def get_seller_by_id_route(seller_id):
      result = seller_service.get_seller_by_id(seller_id)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @seller_bp.route('/me', methods=['PATCH'])
  @jwt_required()
  @roles_required(UserRoles.SELLER) # Only Sellers can update their own profile via /me
  def update_my_seller_profile_route():
      current_user_id = get_jwt_identity()
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      result = seller_service.update_my_seller_profile(current_user_id, data)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @seller_bp.route('/<int:seller_id>', methods=['PATCH'])
  @jwt_required()
  @roles_required(UserRoles.ADMIN) # Only Admins can update any seller profile by ID
  def update_seller_by_id_route(seller_id):
      data = request.get_json()
      if not data:
          return create_response(status="error", message="Request body must be JSON"), 400

      result = seller_service.update_seller_by_id(seller_id, data)
      status_code = result.get('status_code', 500)
      return create_response(**result), status_code

  @seller_bp.route('/<int:seller_id>', methods=['DELETE'])
  @jwt_required()
  @roles_required(UserRoles.ADMIN) # Only Admins can delete seller profiles
  def delete_seller_route(seller_id):
      result = seller_service.delete_seller(seller_id)
      status_code = result.get('status_code', 500)
      # For successful deletion, standard practice is 204 No Content
      if result.get('status') == 'success' and status_code == 200:
          return '', 204 # Return empty body with 204 status
      return create_response(**result), status_code

  # Register blueprint in app factory (e.g., in app/__init__.py)
  # from .routes.seller_route import seller_bp
  # app.register_blueprint(seller_bp)
  ```

- **Responsibilities:** Defines API endpoints according to `crud_guide.md`, handles HTTP requests/responses, parses request data and JWT identity, calls the `SellerService`, applies security decorators (`@jwt_required`, `@roles_required`), and formats the final JSON output using `create_response`.

## 5. Key Considerations & Error Handling

- **Role-Based Access Control (RBAC):**
  - **Public Read:** Listing all sellers (`/`), getting a specific seller (`/<id>`).
  - **Create (`POST /`):** Requires authentication (`@jwt_required`). Any authenticated user can attempt creation; the service layer prevents duplicates per user. Consider adding logic to update the `User`'s role to `Seller`.
  - **Read Own Profile (`GET /me`):** Requires authentication and `Seller` or `Admin` role.
  - **Update Own Profile (`PATCH /me`):** Requires authentication and `Seller` role.
  - **Admin Update/Delete (`PATCH /<id>`, `DELETE /<id>`):** Requires authentication and `Admin` role.
- **Input Validation:**
  - Performed in `SellerService` via `validate_seller_input`.
  - Ensures `name` is present (on create), non-empty. Validates `location` if provided.
  - Returns 400 Bad Request for validation errors.
- **Uniqueness Constraint:**
  - The `user_id` field has a unique constraint (`uq_seller_user_id`).
  - The `create_seller` service method explicitly checks for an existing profile for the `current_user_id` before attempting creation, returning a 409 Conflict.
  - `IntegrityError` is caught during commit as a fallback for race conditions.
- **Error Handling Strategy:**
  - **Service Layer:** Returns dictionaries with `status`, `message`, `data`, `error`, `errors`, and `status_code`.
  - **Route Layer:** Uses `create_response` to format JSON. Handles basic request errors (e.g., non-JSON body) and implements 204 No Content for successful deletions.
- **Relationship Management (Deletion):**
  - **CRITICAL:** Deleting a `Seller` **will automatically delete all associated `Book` records** due to `cascade="all, delete-orphan"` on the `Seller.books` relationship and the non-nullable `Book.seller_id`. This is irreversible data loss for the books. Ensure this is the intended behavior.
  - If books should _not_ be deleted when a seller is deleted, remove the `cascade="all, delete-orphan"` option from the `Seller.books` relationship in `seller.py`. Then, the `delete_seller` service method would need explicit logic to handle the books (e.g., prevent seller deletion if books exist, reassign books, or set `seller_id` to a placeholder if the FK was nullable - which it isn't here).
  - Consider reverting the associated `User`'s role from `Seller` back to `User` upon deletion (see commented-out logic in `delete_seller`).
- **Pagination & Filtering:**
  - Implement in `get_all_sellers` using SQLAlchemy's `paginate()` and filtering/sorting.
  - Accept query parameters (`page`, `per_page`, `search`, `sort_by`, `order`) in the route.
- **Serialization (`to_dict()`):**
  - Implement `to_dict()` and `to_simple_dict()` on `Seller`. Ensure related models (`Book`, `User`) also have appropriate serialization methods. Control the inclusion of related data (`include_books`, `include_user`) based on the context (e.g., public list vs. owner's profile view).

By following these steps, you can implement robust CRUD operations for the Seller model, consistent with the application's architecture, the `crud_guide.md`, and careful consideration of relationship side effects.
