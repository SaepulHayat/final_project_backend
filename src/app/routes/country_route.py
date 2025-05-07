from flask import Blueprint, request, jsonify
from ..services.country_service import CountryService
from ..utils.response import create_response
from ..utils.decorators import role_required
from ..utils.roles import UserRoles
import logging

logger = logging.getLogger(__name__)

country_bp = Blueprint('countries', __name__, url_prefix='/api/v1/countries')
country_service = CountryService()

@country_bp.route('/', methods=['POST'])
@role_required([UserRoles.ADMIN.value]) # Admin role required
def create_country_route():
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400
    result = country_service.create_country(data)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@country_bp.route('/', methods=['GET'])
# Public endpoint (Guest, User, Seller, Admin allowed)
def get_countries_route():
    args = request.args
    result = country_service.get_all_countries(args)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@country_bp.route('/<int:country_id>', methods=['GET'])
# Public endpoint
def get_country_by_id_route(country_id):
    result = country_service.get_country_by_id(country_id)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@country_bp.route('/<int:country_id>/states', methods=['GET'])
# Public endpoint (assuming, adjust roles as needed)
def get_states_by_country_route(country_id):
    args = request.args
    result = country_service.get_states_by_country(country_id, args)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@country_bp.route('/<int:country_id>', methods=['PATCH']) # Typically PATCH for partial updates
@role_required([UserRoles.ADMIN.value]) # Admin role required
def update_country_route(country_id):
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400
    result = country_service.update_country(country_id, data)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@country_bp.route('/<int:country_id>', methods=['DELETE'])
@role_required([UserRoles.ADMIN.value]) # Admin role required
def delete_country_route(country_id):
    result = country_service.delete_country(country_id)
    status_code = result.get('status_code', 500)
    if result.get('status') == 'success' and status_code == 200:
        return "", 204 # Return empty body with 204 status for successful deletion
    return create_response(**result), status_code

# Routes will be added here