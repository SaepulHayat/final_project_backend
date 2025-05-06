from flask import Blueprint, request, jsonify
from ..services.category_service import CategoryService
from ..utils.response import create_response
from ..utils.decorators import role_required
from ..utils.roles import UserRoles
import logging

logger = logging.getLogger(__name__)

category_bp = Blueprint('categories', __name__, url_prefix='/api/v1/categories')
category_service = CategoryService()

@category_bp.route('/', methods=['POST'])
@role_required([UserRoles.ADMIN.value]) # Only Admins can create categories
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
# Public endpoint - no @jwt_required or @role_required
def get_categories_route():
    args = request.args # For pagination/filtering/searching
    result = category_service.get_all_categories(args)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@category_bp.route('/<int:category_id>', methods=['GET'])
# Public endpoint
def get_category_by_id_route(category_id):
    result = category_service.get_category_by_id(category_id)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@category_bp.route('/<int:category_id>/books', methods=['GET'])
# Public endpoint
def get_books_by_category_route(category_id):
    args = request.args # For pagination
    result = category_service.get_books_by_category(category_id, args)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@category_bp.route('/<int:category_id>', methods=['PATCH', 'PUT']) # Allow PUT for full replacement semantics if desired
@role_required([UserRoles.ADMIN.value]) # Only Admins can update categories
def update_category_route(category_id):
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    result = category_service.update_category(category_id, data)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@category_bp.route('/<int:category_id>', methods=['DELETE'])
@role_required([UserRoles.ADMIN.value]) # Only Admins can delete categories
def delete_category_route(category_id):
    result = category_service.delete_category(category_id)
    status_code = result.get('status_code', 500)

    # For successful deletion, standard practice is 204 No Content
    if result.get('status') == 'success' and status_code == 200:
        return "", 204 # Return empty body with 204 status
    return create_response(**result), status_code