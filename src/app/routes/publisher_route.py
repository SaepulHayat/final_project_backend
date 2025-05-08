from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from ..services.publisher_service import PublisherService
from ..utils.response import create_response # Use create_response to handle service responses
from ..utils.decorators import role_required # Assuming role_required exists
from ..utils.roles import UserRoles # Assuming UserRoles enum exists
import logging

logger = logging.getLogger(__name__)
publisher_bp = Blueprint('publishers', __name__, url_prefix='/api/v1/publishers')
publisher_service = PublisherService()

@publisher_bp.route('/', methods=['POST'])
@role_required([UserRoles.SELLER]) # Admins or Sellers can create
def create_publisher_route():
    # Consider adding check: If user is Seller, maybe restrict fields? (Future enhancement)
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    result = publisher_service.create_publisher(data)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@publisher_bp.route('/', methods=['GET'])
# Public endpoint - no @jwt_required or @role_required
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
@role_required([UserRoles.SELLER.value]) # Only Admins can update
@role_required([UserRoles.SELLER.value]) # Only Admins can update
def update_publisher_route(publisher_id):
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    result = publisher_service.update_publisher(publisher_id, data)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@publisher_bp.route('/<int:publisher_id>', methods=['DELETE'])
@role_required([UserRoles.SELLER.value]) # Only Admins can delete
@role_required([UserRoles.SELLER.value]) # Only Admins can delete
def delete_publisher_route(publisher_id):
    result = publisher_service.delete_publisher(publisher_id)
    status_code = result.get('status_code', 500)
    # For successful deletion, standard practice is 204 No Content
    if result.get('status') == 'success' and status_code == 200:
        return '', 204 # Return empty body with 204 status
    return create_response(**result), status_code