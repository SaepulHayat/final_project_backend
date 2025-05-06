from flask import Blueprint, request, jsonify  
from flask_jwt_extended import jwt_required, get_jwt  
from ..services.auth_service import AuthService  
from ..utils.validators import validate_register_input, validate_login_input  
from ..utils.response import create_response, error_response, success_response
from ..extensions import db 
import logging  
from typing import Dict, Any  

logger = logging.getLogger(__name__)  
auth_bp = Blueprint('auth', __name__)  
auth_service = AuthService()  

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json(silent=True)
        if not data:
            # Handle case where request body is not JSON or empty
            return create_response(status="error", message="Request body must be JSON"), 400

        result = auth_service.register_user(data)
        # Get status code from service response, default to 500 if missing (though service should always provide it now)
        status_code = result.get('status_code', 500)
        # Use create_response to format the entire response based on the service result
        return create_response(**result), status_code

    except Exception as e:
        logger.error(f"Unexpected error in register: {e}", exc_info=True)
        # Use create_response for consistent error formatting
        return create_response(status="error", message="An unexpected error occurred during registration"), 500


@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json(silent=True)
        if not data:
            return create_response(status="error", message="Request body must be JSON"), 400

        result = auth_service.login_user(data)
        status_code = result.get('status_code', 500) # Default to 500, but expect 200 or 401 from service
        return create_response(**result), status_code

    except Exception as e:
        logger.error(f"Unexpected error in login: {e}", exc_info=True)
        return create_response(status="error", message="An unexpected error occurred during login"), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        jwt_payload = get_jwt() # Renamed for clarity
        jti = jwt_payload['jti']

        result = auth_service.logout_user(jti)
        status_code = result.get('status_code', 500) # Default to 500, but expect 200 or 500 from service
        return create_response(**result), status_code

    except Exception as e:
        logger.error(f"Unexpected error in logout: {e}", exc_info=True)
        return create_response(status="error", message="An unexpected error occurred during logout"), 500
