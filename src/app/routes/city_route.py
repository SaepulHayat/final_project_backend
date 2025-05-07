from flask import Blueprint, request, jsonify
from ..services.city_service import CityService
from ..utils.response import create_response
from ..utils.decorators import role_required
from ..utils.roles import UserRoles
import logging

logger = logging.getLogger(__name__)

city_bp = Blueprint('cities', __name__, url_prefix='/api/v1/cities')
city_service = CityService()

@city_bp.route('/', methods=['POST'])
@role_required([UserRoles.ADMIN.value])  # Assuming UserRoles is defined elsewhere
def create_city_route():
    """Creates a new city."""
    data = request.get_json()
    if not data:
        # Use create_response for error formatting
        return create_response(status="error", message="Request body must be JSON"), 400

    result = city_service.create_city(data)
    # Extract status_code for the Flask response tuple
    status_code = result.pop('status_code', 500)
    # Pass the rest of the result dict to create_response
    return create_response(**result), status_code

@city_bp.route('/', methods=['GET'])
# Public endpoint - no @jwt_required or @admin_required
def get_cities_route():
    """Gets a list of cities with pagination, filtering, sorting."""
    args = request.args # For pagination/filtering/searching/sorting
    result = city_service.get_all_cities(args)
    status_code = result.pop('status_code', 500)
    return create_response(**result), status_code

@city_bp.route('/<int:city_id>', methods=['GET'])
# Public endpoint
def get_city_by_id_route(city_id):
    """Gets a specific city by its ID."""
    result = city_service.get_city_by_id(city_id)
    status_code = result.pop('status_code', 500)
    return create_response(**result), status_code

@city_bp.route('/<int:city_id>', methods=['PATCH']) # PATCH is generally preferred for partial updates
@role_required([UserRoles.ADMIN.value])  # Assuming UserRoles is defined elsewhere
def update_city_route(city_id):
    """Updates an existing city."""
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    result = city_service.update_city(city_id, data)
    status_code = result.pop('status_code', 500)
    return create_response(**result), status_code

@city_bp.route('/<int:city_id>', methods=['DELETE'])
@role_required([UserRoles.ADMIN.value])  # Assuming UserRoles is defined elsewhere
def delete_city_route(city_id):
    """Deletes a city."""
    result = city_service.delete_city(city_id)
    status_code = result.pop('status_code', 500)

    # For successful deletion, return 204 No Content
    if result.get('status') == 'success' and status_code == 200:
        # Return empty body and 204 status code directly
        return "", 204
    # For errors or unexpected success status codes, format with create_response
    return create_response(**result), status_code