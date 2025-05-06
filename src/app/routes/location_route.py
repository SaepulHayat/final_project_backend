# src/app/routes/location_route.py
from flask import Blueprint, request, jsonify
from ..services.location_service import LocationService
from ..utils.response import create_response # Use create_response
from ..utils.decorators import role_required # Import decorators
from flask_jwt_extended import get_jwt_identity, get_jwt, jwt_required # To get user info for authorization
from ..utils.roles import UserRoles # Assuming UserRoles enum
import logging

logger = logging.getLogger(__name__)

location_bp = Blueprint('locations', __name__, url_prefix='/api/v1/locations')
location_service = LocationService()

@location_bp.route('/', methods=['POST'])
@role_required # Only Admins can create locations directly via this endpoint
def create_location_route():
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    result = location_service.create_location(data)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@location_bp.route('/', methods=['GET'])
@jwt_required()
def get_locations_route():
    args = request.args # For pagination/filtering/searching
    # Need role to pass to service for authorization check
    jwt_data = get_jwt() # Get JWT payload
    user_role = jwt_data.get('role', None) # Assuming role is in JWT claims

    result = location_service.get_all_locations(args, user_role)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@location_bp.route('/<int:location_id>', methods=['GET'])
@jwt_required()
# Authorization logic (Admin or Owner) is inside the service
def get_location_by_id_route(location_id):
    current_user_id = get_jwt_identity() # Get user ID from JWT
    jwt_data = get_jwt() # Get JWT payload
    user_role = jwt_data.get('role', None) # Assuming role is in JWT claims

    result = location_service.get_location_by_id(location_id, current_user_id, user_role)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@location_bp.route('/<int:location_id>', methods=['PATCH'])
# Authorization logic (Admin or Owner, with field restrictions) is inside the service
def update_location_route(location_id):
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    current_user_id = get_jwt_identity() # Get user ID from JWT
    jwt_data = get_jwt() # Get JWT payload
    user_role = jwt_data.get('role', None) # Assuming role is in JWT claims

    result = location_service.update_location(location_id, data, current_user_id, user_role)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@location_bp.route('/<int:location_id>', methods=['DELETE'])
@role_required([UserRoles.ADMIN.value]) # Only Admins can delete locations
def delete_location_route(location_id):
    result = location_service.delete_location(location_id)
    status_code = result.get('status_code', 500)

    if result.get('status') == 'success' and status_code == 200:
        return "", 204

    if status_code == 409:
        return create_response(**result), status_code

    return create_response(**result), status_code