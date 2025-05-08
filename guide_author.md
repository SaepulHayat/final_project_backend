# Guide: Implementing Author CRUD Operations

This guide details how to implement Create, Read, Update, and Delete (CRUD) operations for the Author model, adhering to the layered architecture outlined in crud_plan_2.md.

**Reference:**

- Author Model: src/app/model/author.py (Uses full_name)

## 1. Model Layer (src/app/model/author.py)

- **Existing Model:** The Author model uses `id`, `full_name` (required), `bio`, and has a relationship `books = db.relationship('Book', back_populates='author', lazy='dynamic')`.
- **Responsibilities:** Defines the data structure and database mapping for authors.

## 2. Utility Layer (src/app/utils/)

- **Validators (validators.py):**
  - Create a validation function: `validate_author_input(data, is_update=False)`
    - Checks: `full_name` is present and non-empty. `bio` might have length constraints.
    - Return a dictionary of errors if validation fails, otherwise `None`.
- **Response Formatting (response.py):**
  - Utilize the existing `success_response` and `error_response` functions for consistent API responses.
- **Decorators (decorators.py):**
  - Use `@jwt_required()` for endpoints requiring authentication.
  - Implement or use a role-checking decorator (e.g., `@roles_required(UserRoles.ADMIN, UserRoles.SELLER)`) to enforce permissions as defined in crud_guide.md.

## 3. Service Layer (src/app/services/author_service.py)

- **Create AuthorService Class:**

```python
from ..model.author import Author
from ..extensions import db
from ..utils.validators import validate_author_input
from ..utils.response import success_response, error_response # Or handle errors via exceptions
from sqlalchemy import func # Import func for case-insensitive comparison
import logging

logger = logging.getLogger(__name__)

class AuthorService:
    def create_author(self, data):
        errors = validate_author_input(data)
        if errors:
            # Option 1: Return error dict (as used in auth_service)
            return error_response("Validation failed", errors=errors)
            # Option 2: Raise a custom validation exception
            # raise ValidationException("Validation failed", errors=errors)

        # Check for name uniqueness (case-insensitive)
        full_name = data.get('full_name')
        existing_author = Author.query.filter(
            func.lower(Author.full_name) == func.lower(full_name)
        ).first()
        if existing_author:
            return error_response("Author with this name already exists",
error="duplicate_name")

        new_author = Author(
            full_name=full_name,
            bio=data.get('bio')
        )
        try:
            db.session.add(new_author)
            db.session.commit()
            # Return success with author data, excluding sensitive info if any
            return success_response("Author created successfully",
data=new_author.to_dict()) # Assuming a to_dict() method
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating author: {e}", exc_info=True)
            return error_response("Failed to create author", error=str(e))

    def get_all_authors(self, args):
        # Implement pagination, filtering (e.g., by name), searching
        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)
        search_term = args.get('search')

        query = Author.query

        if search_term:
            # Search across full_name (case-insensitive)
            query = query.filter(Author.full_name.ilike(f'%{search_term}%'))

        paginated_authors = query.paginate(page=page, per_page=per_page,
error_out=False)

        return success_response(
            "Authors retrieved successfully",
            data={
                "authors": [author.to_dict() for author in paginated_authors.items],
                "total": paginated_authors.total,
                "pages": paginated_authors.pages,
                "current_page": paginated_authors.page
            }
        )

    def get_author_by_id(self, author_id):
        author = Author.query.get(author_id)
        if not author:
            return error_response("Author not found", error="not_found")
        return success_response("Author found", data=author.to_dict())

    def get_books_by_author(self, author_id, args):
        author = Author.query.get(author_id)
        if not author:
            return error_response("Author not found", error="not_found")

        # Implement pagination for books if needed
        # books = [book.to_simple_dict() for book in author.books] # Assuming Book model
# has relationship and dict method
        # return success_response("Books by author retrieved", data={"books": books})
        # --- Placeholder for actual book retrieval logic ---
        return success_response("Books by author retrieved", data={"books": []})


    def update_author(self, author_id, data):
        author = Author.query.get(author_id)
        if not author:
            return error_response("Author not found", error="not_found")

        errors = validate_author_input(data, is_update=True) # Allow partial updates
        if errors:

            return error_response("Validation failed", errors=errors)

        # Check for name uniqueness if full_name is being updated
        if 'full_name' in data and data['full_name'].lower() != author.full_name.lower():
            existing_author = Author.query.filter(
                func.lower(Author.full_name) == func.lower(data['full_name']),
                Author.id != author_id # Exclude the current author
            ).first()
            if existing_author:
                return error_response("Another author with this name already exists",
error="duplicate_name")
            author.full_name = data['full_name'] # Update only if validation passes

        # Update other fields if provided in data
        if 'bio' in data:
            author.bio = data['bio']

        try:
            db.session.commit()
            return success_response("Author updated successfully", data=author.to_dict())
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating author {author_id}: {e}", exc_info=True)
            return error_response("Failed to update author", error=str(e))

    def delete_author(self, author_id):
        author = Author.query.get(author_id)
        if not author:
            return error_response("Author not found", error="not_found")

        # **Relationship Handling:** Check if deletion is allowed based on relationships
        # Example: If books are associated and cascade isn't set to delete them
        # Because lazy='dynamic', author.books is a query object. Execute it.
        if author.books.first():
            return error_response("Cannot delete author with associated books",
error="conflict")

        try:
            db.session.delete(author)
            db.session.commit()
            return success_response("Author deleted successfully")
        except Exception as e: # Catch potential IntegrityError if DB prevents deletion
            db.session.rollback()

            logger.error(f"Error deleting author {author_id}: {e}", exc_info=True)
            # Check if it's a foreign key constraint violation (requires importing sqlalchemy)
            # import sqlalchemy
            # if isinstance(e, sqlalchemy.exc.IntegrityError):
            #    return error_response("Cannot delete author due to existing references (e.g.,
# books)", error="conflict")
            return error_response("Failed to delete author", error=str(e))
```

- **Responsibilities:** Encapsulates all business logic related to authors, interacts with the database via the Author model, performs validation (using full_name), and handles specific errors.

## 4. Route Layer (src/app/routes/author_route.py)

- **Create Blueprint and Import Services/Utils:**

```python
from flask import Blueprint, request, jsonify
from ..services.author_service import AuthorService
from ..utils.response import create_response # Use create_response to jsonify service
# responses
from ..utils.decorators import jwt_required, roles_required # Assuming roles_required
# exists
from ..utils.roles import UserRoles # Assuming UserRoles enum exists
import logging

logger = logging.getLogger(__name__)
author_bp = Blueprint('authors', __name__, url_prefix='/api/v1/authors')
author_service = AuthorService()

@author_bp.route('/', methods=['POST'])
@jwt_required()
@roles_required(UserRoles.ADMIN, UserRoles.SELLER) # Example role check
def create_author_route():
    data = request.get_ json()
    if not data:
        return create_response("error", "Request body must be JSON"), 400

    result = author_service.create_author(data)
    status_code = 201 if result.get('status') == 'success' else 400 # Or determine based
# on error type
    if result.get('error') == 'duplicate_name':
        status_code = 409 # Conflict for duplicate name
    return create_response(**result), status_code # Unpack dict into create_response


@author_bp.route('/', methods=['GET'])
def get_authors_route():
    args = request.args # For pagination/filtering/searching
    result = author_service.get_all_authors(args)
    # Public endpoint, usually success unless server error
    status_code = 200 if result.get('status') == 'success' else 500
    return create_response(**result), status_code

@author_bp.route('/<int:author_id>', methods=['GET'])
def get_author_by_id_route(author_id):
    result = author_service.get_author_by_id(author_id)
    status_code = 200
    if result.get('status') == 'error':
        status_code = 404 if result.get('error') == 'not_found' else 500
    return create_response(**result), status_code

@author_bp.route('/<int:author_id>/books', methods=['GET'])
def get_books_by_author_route(author_id):
    args = request.args
    result = author_service.get_books_by_author(author_id, args)
    status_code = 200
    if result.get('status') == 'error':
        status_code = 404 if result.get('error') == 'not_found' else 500
    return create_response(**result), status_code


@author_bp.route('/<int:author_id>', methods=['PATCH']) # Changed PUT to PATCH for
# partial updates
@jwt_required()
@roles_required(UserRoles.ADMIN)
def update_author_route(author_id):
    data = request.get_ json()
    if not data:
        return create_response("error", "Request body must be JSON"), 400

    result = author_service.update_author(author_id, data)
    status_code = 200
    if result.get('status') == 'error':
        if result.get('error') == 'not_found':
            status_code = 404
        elif 'Validation failed' in result.get('message', ''):
            status_code = 400

        elif result.get('error') == 'duplicate_name':
            status_code = 409 # Conflict for duplicate name
        else:
            status_code = 500 # Or specific code based on error
    return create_response(**result), status_code

@author_bp.route('/<int:author_id>', methods=['DELETE'])
@jwt_required()
@roles_required(UserRoles.ADMIN)
def delete_author_route(author_id):
    result = author_service.delete_author(author_id)
    status_code = 200 # Or 204 No Content on successful delete
    if result.get('status') == 'error':
        if result.get('error') == 'not_found':
            status_code = 404
        elif result.get('error') == 'conflict':
            status_code = 409 # Conflict if deletion is blocked
        else:
            status_code = 500
    return create_response(**result), status_code

# Register blueprint in app factory (e.g., in app/__init__.py)
# from .routes.author_route import author_bp
# app.register_blueprint(author_bp)
```

- **Responsibilities:** Defines API endpoints, handles HTTP request/response cycle, parses request data, calls the AuthorService, applies security decorators, and uses response.py utilities to format the final JSON output.

## 5. Key Considerations & Error Handling

- **Role-Based Access Control (RBAC):**
  - Strictly enforce roles specified in crud_guide.md using decorators (`@roles_required`) on route functions.
  - Ensure the decorator correctly checks the JWT claims for user roles.
- **Input Validation:**
  - Perform validation within the AuthorService using `validate_author_input` (checking `full_name`).
  - Return clear error messages (e.g., `{"errors": {"full_name": "Full name cannot be empty"}}`) with a 400 Bad Request status from the route.
- **Error Handling Strategy:**
  - **Service Layer:** Can return error dictionaries (like auth_service) or raise custom exceptions (e.g., `NotFoundException`, `ValidationException`, `ConflictException`). Raising exceptions can sometimes lead to cleaner route code if handled by Flask error handlers. Returning dicts keeps logic contained within the service call flow. Choose one approach and be consistent.
  - **Route Layer:**
    - Catches results/exceptions from the service layer.
    - Maps service results/errors to appropriate HTTP status codes (400, 401, 403, 404, 409, 500).
    - Uses `create_response` to format the final JSON response.
    - Include a generic `try...except` in routes for unexpected errors, logging them and returning a 500 Internal Server Error.
- **Relationship Management (Deletion):**
  - The `delete_author` service method must consider the relationship with Book.
  - **Strategy 1 (Check Before Delete):** Query if any books are linked to the author (if `author.books.first():`). If so, return a 409 Conflict error response, preventing deletion. (Implemented in example)
  - **Strategy 2 (Rely on DB Cascade):** If the `db.relationship` in Book model is configured with `cascade="all, delete-orphan"` or similar, the database might handle deleting associated books. This is often dangerous for core data like authors.
  - **Strategy 3 (Set Foreign Key to Null):** If the `Book.author_id` foreign key is nullable, configure the relationship to set `author_id` to NULL on author deletion.
  - **Recommendation:** Strategy 1 (Check Before Delete) is often the safest for entities like Authors. Clearly document the chosen behavior. The service should handle potential `IntegrityError` from the database if a constraint prevents deletion.
- **Pagination & Filtering:**
  - Implement in the `get_all_authors` service method using SQLAlchemy's `paginate()` and filtering capabilities (`.filter()`, `.ilike()` on `full_name`).
  - Accept query parameters (`page`, `per_page`, `search`, etc.) in the corresponding route function (`request.args`).
- **Serialization (to_dict()):**
  - Implement a `to_dict()` method on the Author model to control which fields are included in API responses, avoiding accidental exposure of sensitive data.

By following these steps, you can implement robust and maintainable CRUD operations for the Author model, consistent with the application's overall architecture and the author.py model structure.
