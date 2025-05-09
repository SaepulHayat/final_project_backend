from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity # To get current user ID
from ..services.rating_service import RatingService
from ..utils.response import create_response
from ..utils.decorators import role_required # Assuming role_required exists
from ..utils.roles import UserRoles # Assuming UserRoles enum exists
from ..model.user import User # To get user role
import logging

logger = logging.getLogger(__name__)

# --- Blueprint for /books/{book_id}/ratings ---
book_ratings_bp = Blueprint('book_ratings', __name__, url_prefix='/api/v1/books/<int:book_id>/ratings')
rating_service = RatingService() # Instantiate service

@book_ratings_bp.route('/', methods=['POST'])
@role_required([UserRoles.CUSTOMER.value, UserRoles.SELLER.value])
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
@role_required([UserRoles.CUSTOMER.value, UserRoles.SELLER.value])
def get_my_ratings_route():
    user_identity = get_jwt_identity()
    user_id = user_identity.get('id') if isinstance(user_identity, dict) else user_identity
    args = request.args
    result = rating_service.get_ratings_by_user(user_id, args)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@user_ratings_bp.route('/<int:user_id>/ratings', methods=['GET'])
@role_required([UserRoles.SELLER.value]) # Only Admins can view others' ratings by user ID
@role_required([UserRoles.SELLER.value]) # Only Admins can view others' ratings by user ID
def get_user_ratings_route(user_id):
    args = request.args
    result = rating_service.get_ratings_by_user(user_id, args)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

# --- Blueprint for /ratings/{rating_id} ---
ratings_bp = Blueprint('ratings', __name__, url_prefix='/api/v1/ratings')

@ratings_bp.route('/<int:rating_id>', methods=['GET'])
# Public endpoint - No @jwt_required or role_required needed
def get_rating_by_id_route(rating_id):
    result = rating_service.get_rating_by_id(rating_id) # Service call remains, user context is optional in service
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@ratings_bp.route('/<int:rating_id>', methods=['PATCH'])
@role_required([UserRoles.CUSTOMER.value, UserRoles.SELLER.value])
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
@role_required([UserRoles.CUSTOMER.value, UserRoles.SELLER.value])
def delete_rating_route(rating_id):
    user_identity = get_jwt_identity()
    current_user_id = user_identity.get('id') if isinstance(user_identity, dict) else user_identity
    user = User.query.get(current_user_id)
    if not user:
        return create_response(status="error", message="User not found"), 404
    current_user_role = UserRoles(user.role)

    result = rating_service.delete_rating(rating_id, current_user_id, current_user_role)
    status_code = result.get('status_code', 500)

    if result.get('status') == 'success' and status_code == 200:
        logger.info(f"Rating ID {rating_id} deleted successfully. Returning 204 No Content.") # DEBUG LOG
        return '', 204
    logger.warning(f"Rating ID {rating_id} deletion service call did not return expected success/200. Result: {result}, Status Code: {status_code}. Returning full response.") # DEBUG LOG
    return create_response(**result), status_code