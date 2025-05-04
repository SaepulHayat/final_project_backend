from flask import Blueprint, request, jsonify
from ..services.author_service import AuthorService
from ..utils.response import create_response # Using create_response to handle jsonify directly
# from flask_jwt_extended import jwt_required # Add later if needed for specific routes
# from ..utils.decorators import roles_required # Add later for role-based access
# from ..utils.roles import UserRoles # Add later for role constants
import logging

logger = logging.getLogger(__name__)
author_bp = Blueprint('authors', __name__, url_prefix='/authors')
author_service = AuthorService()

@author_bp.route('', methods=['POST'])
# @jwt_required() # Example: Protect this route later
# @roles_required(UserRoles.ADMIN, UserRoles.SELLER) # Example: Restrict access later
def create_author_route():
    """
    Route to create a new author.
    Expects JSON payload with first_name, last_name (optional), bio (optional).
    """
    try:
        data = request.get_json()
        if not data:
            return create_response("error", "Request body must be JSON"), 400

        result = author_service.create_author(data)

        if result.get('status') == 'success':
            # Use create_response which includes jsonify
            return create_response(
                status="success",
                message=result.get('message'),
                data=result.get('data')
            ), 201 # 201 Created status code
        else:
            # Use create_response which includes jsonify
            return create_response(
                status="error",
                message=result.get('message'),
                error=result.get('error') # Pass potential specific error message
            ), 400 # 400 Bad Request status code

    except Exception as e:
        logger.error(f"Error in create_author_route: {str(e)}", exc_info=True)
        # Use create_response which includes jsonify
        return create_response(
            status="error",
            message="An unexpected error occurred" # Added missing message
        ), 500 # 500 Internal Server Error

@author_bp.route('/<int:author_id>', methods=['GET'])
# @jwt_required() # Public route as per plan
def get_author_by_id_route(author_id):
    """
    Route to get a specific author by their ID.
    """
    try:
        result = author_service.get_author_by_id(author_id)

        if result.get('status') == 'success':
            return create_response(
                status="success",
                message=result.get('message'),
                data=result.get('data')
            ), 200 # 200 OK
        elif result.get('message') == 'Author not found':
            return create_response(
                status="error",
                message=result.get('message')
            ), 404 # 404 Not Found
        else:
            # Handle other potential errors from the service layer
            return create_response(
                status="error",
                message=result.get('message'),
                error=result.get('error')
            ), 500 # Or appropriate error code based on service error

    except Exception as e:
        logger.error(f"Error in get_author_by_id_route for ID {author_id}: {str(e)}", exc_info=True)
        return create_response(
            status="error",
            message="An unexpected error occurred"
        ), 500
@author_bp.route('', methods=['GET'])
# @jwt_required() # Public route as per plan
def get_all_authors_route():
    """
    Route to get a list of all authors with pagination and search.
    Query Parameters:
        page (int, optional): Page number (default: 1).
        per_page (int, optional): Items per page (default: 10).
        search (str, optional): Search term for first/last name.
    """
    try:
        # Get query parameters with defaults
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', None, type=str)

        # Ensure positive page and per_page values
        if page < 1: page = 1
        if per_page < 1: per_page = 1
        # Optional: Add a max limit for per_page
        # if per_page > 100: per_page = 100

        result = author_service.get_all_authors(page=page, per_page=per_page, search=search)

        if result.get('status') == 'success':
            return create_response(
                status="success",
                message=result.get('message'),
                data=result.get('data') # Contains 'authors' list and 'pagination' info
            ), 200 # 200 OK
        else:
            # Handle potential errors from the service layer
            return create_response(
                status="error",
                message=result.get('message'), # Complete the return statement
                error=result.get('error')
            ), 500 # Or appropriate error code

    except Exception as e:
        logger.error(f"Error in get_all_authors_route: {str(e)}", exc_info=True)
        return create_response(
            status="error",
            message="An unexpected error occurred"
        ), 500

# Correctly indented update route
@author_bp.route('/<int:author_id>', methods=['PUT', 'PATCH']) # Allow both PUT and PATCH
# @jwt_required() # Protect this route
# @roles_required(UserRoles.ADMIN) # Example: Only Admins can update any author
def update_author_route(author_id):
    """
    Route to update an existing author.
    Expects JSON payload with fields to update (first_name, last_name, bio).
    """
    try:
        data = request.get_json()
        if not data:
            return create_response("error", "Request body must be JSON"), 400

        # Basic check: Ensure at least one field is provided for update
        if not any(key in data for key in ['first_name', 'last_name', 'bio']):
            return create_response("error", "No update data provided in request body"), 400

        result = author_service.update_author(author_id, data)

        if result.get('status') == 'success':
            return create_response(
                status="success",
                message=result.get('message'),
                data=result.get('data')
            ), 200 # 200 OK
        elif result.get('message') == 'Author not found':
            return create_response(
                status="error",
                message=result.get('message')
            ), 404 # 404 Not Found
        elif result.get('message') == 'No update data provided':
            return create_response(
                status="error",
                message=result.get('message')
            ), 400 # 400 Bad Request
        else:
            # Handle other potential errors from the service layer
            return create_response(
                status="error",
                message=result.get('message'), # Complete the return statement
                error=result.get('error')
            ), 500 # Or appropriate error code

    except Exception as e:
        logger.error(f"Error in update_author_route for ID {author_id}: {str(e)}", exc_info=True)
        return create_response(
            status="error",
            message="An unexpected error occurred"
        ), 500

# Correctly indented delete route
@author_bp.route('/<int:author_id>', methods=['DELETE'])
# @jwt_required() # Protect this route
# @roles_required(UserRoles.ADMIN) # Example: Only Admins can delete authors
def delete_author_route(author_id):
    """
    Route to delete an author.
    """
    try:
        result = author_service.delete_author(author_id)

        if result.get('status') == 'success':
            # Return 204 No Content on successful deletion is common practice
            # Or return 200 OK with the success message
            return create_response(
                status="success",
                message=result.get('message')
                # No data payload needed for delete
            ), 200 # Or 204
        elif result.get('message') == 'Author not found':
            return create_response(
                status="error",
                message=result.get('message')
            ), 404 # 404 Not Found
        else:
            # Handle other potential errors from the service layer
            return create_response(
                status="error",
                message=result.get('message'),
                error=result.get('error')
            ), 500 # Or appropriate error code

    except Exception as e:
        logger.error(f"Error in delete_author_route for ID {author_id}: {str(e)}", exc_info=True)
        return create_response(
            status="error",
            message="An unexpected error occurred"
        ), 500
# Removed duplicated except block and comment

# --- Placeholder for other CRUD routes ---

# GET /authors (List all)
# GET /authors/<int:author_id> (Get one)
# PUT /authors/<int:author_id> (Update one)
# DELETE /authors/<int:author_id> (Delete one)