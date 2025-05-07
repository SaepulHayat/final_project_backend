# src/app/routes/location_route.py
from flask import Blueprint, request, jsonify
from ..services.location_service import LocationService
from ..utils.response import create_response
from ..utils.decorators import role_required
from flask_jwt_extended import get_jwt_identity, get_jwt
from ..utils.roles import UserRoles # Assuming UserRoles enum
import logging

logger = logging.getLogger(__name__)

location_bp = Blueprint('locations', __name__, url_prefix='/api/v1/locations')
location_service = LocationService()

@location_bp.route('/', methods=['POST'])
@role_required([UserRoles.ADMIN.value, UserRoles.SELLER.value, UserRoles.CUSTOMER.value])
def create_location_route():
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    current_user_id = get_jwt_identity()
    jwt_data = get_jwt()
    user_role = jwt_data.get('role')

    if user_role is None:
        logger.error(f"User role not found in JWT claims for user_id {current_user_id}. JWT data: {jwt_data}")
        return create_response(status="error", message="User role not found in token. Cannot process request.", error="missing_role_claim"), 403 # Forbidden or Bad Request

    result = location_service.create_location(data, current_user_id, user_role)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@location_bp.route('/', methods=['GET'])
@role_required([UserRoles.ADMIN.value])
def get_locations_route():
    args = request.args
    jwt_data = get_jwt()
    user_role = jwt_data.get('role')

    result = location_service.get_all_locations(args, user_role)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@location_bp.route('/<int:location_id>', methods=['GET'])
@role_required([UserRoles.ADMIN.value, UserRoles.SELLER.value, UserRoles.CUSTOMER.value])
def get_location_by_id_route(location_id):
    current_user_id = get_jwt_identity()
    jwt_data = get_jwt()
    user_role = jwt_data.get('role')

    result = location_service.get_location_by_id(location_id, current_user_id, user_role)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@location_bp.route('/<int:location_id>', methods=['PATCH'])
@role_required([UserRoles.ADMIN.value, UserRoles.SELLER.value, UserRoles.CUSTOMER.value])
def update_location_route(location_id):
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    current_user_id = get_jwt_identity()
    jwt_data = get_jwt()
    user_role = jwt_data.get('role')

    result = location_service.update_location(location_id, data, current_user_id, user_role)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@location_bp.route('/<int:location_id>', methods=['DELETE'])
@role_required([UserRoles.ADMIN.value, UserRoles.SELLER.value, UserRoles.CUSTOMER.value]) # Allow Admin, Seller, Customer
def delete_location_route(location_id):
    current_user_id = get_jwt_identity() # Get user ID from JWT
    jwt_data = get_jwt() # Get JWT payload
    user_role = jwt_data.get('role') # Assuming role is in JWT claims

    # Pass current_user_id and user_role to the service method
    result = location_service.delete_location(location_id, current_user_id, user_role)
    status_code = result.get('status_code', 500)

    if result.get('status') == 'success' and status_code == 200: # Service returns 200 on success
        return "", 204 # Route returns 204

    return create_response(**result), status_code
