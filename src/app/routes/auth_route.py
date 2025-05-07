from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt
import logging

from ..extensions import db
from ..services.auth_service import AuthService
from ..utils.validators import validate_register_input, validate_login_input
from ..utils.response import create_response

# --- Setup ---
logger = logging.getLogger(__name__)
auth_bp = Blueprint('auth', __name__)
auth_service = AuthService()

# --- Routes ---

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json(silent=True)
        if not data:
            return create_response(status="error", message="Request body must be JSON"), 400

        result = auth_service.register_user(data)
        return create_response(**result), result.get('status_code', 500)

    except Exception as e:
        logger.error("Unexpected error in register: %s", e, exc_info=True)
        return create_response(
            status="error",
            message="An unexpected error occurred during registration"
        ), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    try:
        data = request.get_json(silent=True)
        if not data:
            return create_response(status="error", message="Request body must be JSON"), 400

        result = auth_service.login_user(data)
        return create_response(**result), result.get('status_code', 500)

    except Exception as e:
        logger.error("Unexpected error in login: %s", e, exc_info=True)
        return create_response(
            status="error",
            message="An unexpected error occurred during login"
        ), 500

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    try:
        jti = get_jwt().get('jti')
        result = auth_service.logout_user(jti)
        return create_response(**result), result.get('status_code', 500)

    except Exception as e:
        logger.error("Unexpected error in logout: %s", e, exc_info=True)
        return create_response(
            status="error",
            message="An unexpected error occurred during logout"
        ), 500