from flask import Blueprint, request, jsonify
from ..services.state_service import StateService
from ..utils.response import create_response # Use create_response
from ..utils.decorators import role_required
from ..utils.roles import UserRoles
import logging

logger = logging.getLogger(__name__)

state_bp = Blueprint('states', __name__, url_prefix='/api/v1/states')
state_service = StateService()

@state_bp.route('/', methods=['POST'])
@role_required([UserRoles.ADMIN.value])
def create_state_route():
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    result = state_service.create_state(data)
    status_code = result.pop('status_code', 500) # Remove status_code before passing to create_response
    return create_response(**result), status_code

@state_bp.route('/', methods=['GET'])
# Public endpoint - no @jwt_required or @admin_required
def get_states_route():
    args = request.args # For pagination/filtering/sorting/searching
    result = state_service.get_all_states(args)
    status_code = result.pop('status_code', 500)
    return create_response(**result), status_code

@state_bp.route('/<int:state_id>', methods=['GET'])
# Public endpoint
def get_state_by_id_route(state_id):
    result = state_service.get_state_by_id(state_id)
    status_code = result.pop('status_code', 500)
    return create_response(**result), status_code

@state_bp.route('/<int:state_id>/cities', methods=['GET'])
# Public endpoint - Get cities within a specific state
def get_cities_by_state_route(state_id):
    args = request.args # For pagination
    result = state_service.get_cities_by_state(state_id, args)
    status_code = result.pop('status_code', 500)
    return create_response(**result), status_code

@state_bp.route('/<int:state_id>', methods=['PATCH']) # Using PATCH for partial updates
@role_required([UserRoles.ADMIN.value]) # Assuming UserRoles is imported correctly
def update_state_route(state_id):
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    result = state_service.update_state(state_id, data)
    status_code = result.pop('status_code', 500)
    return create_response(**result), status_code

@state_bp.route('/<int:state_id>', methods=['DELETE'])
@role_required([UserRoles.ADMIN.value]) # Assuming UserRoles is imported correctly
def delete_state_route(state_id):
    result = state_service.delete_state(state_id)
    status_code = result.pop('status_code', 500)

    # Handle 204 No Content for successful deletion
    if result.get('status') == 'success' and status_code == 200: # Service signals success with 200
        return "", 204 # Return empty body with 204 status
    # Otherwise, return the JSON response from the service (e.g., 404, 409, 500)
    return create_response(**result), status_code