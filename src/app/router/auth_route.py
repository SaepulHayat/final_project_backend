from flask import Blueprint, request, jsonify  
from flask_jwt_extended import jwt_required, get_jwt  
from ..service.auth_service import AuthService  
from ..util.validators import validate_register_input, validate_login_input  
from ..util.response import create_response, error_response, success_response
from ..extensions import db 
import logging  
from typing import Dict, Any  

logger = logging.getLogger(__name__)  
auth_bp = Blueprint('auth', __name__)  
auth_service = AuthService()  

@auth_bp.route('/register', methods=['POST'])
def register():
    try:
        data = request.get_json(silent=True) or request.form 
        result = auth_service.register_user(data)
        
        print("DEBUG result type:", type(result), "value:", result)

        # Atur status code berdasarkan result
        if result.get('status') == 'success':
            return jsonify(result), 201
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@auth_bp.route('/login', methods=['POST'])
def login(): 
    try:
        data = request.get_json(silent=True) or request.form 
        result = auth_service.login_user(data)
        
        
        print("DEBUG result type:", type(result), "value:", result)
        
        if result['status'] == 'success':
            return success_response(result['message'], result.get('data')), 200
        else:
            return error_response(result['message'], error=result.get('error')), 401
    
    except Exception as e:
        logger.error("Login error: %s", str(e), exc_info=True)
        return error_response("Internal server error"), 500
    
@auth_bp.route('/logout', methods=['POST'])  
@jwt_required()  
def logout():  
    try:  
        token = get_jwt()  
        
        result = auth_service.logout_user(token['jti'])  
        
        if result.get('status') == 'success':  
            return create_response(  
                status="success",   
                message=result.get('message')  
            ), 200
        
        return create_response(  
            status="error",   
            message=result.get('message', 'Logout failed')  
        ), 401
    
    except Exception as e:  
        logger.error(f"Unexpected error in logout: {e}", exc_info=True)  
        return create_response(  
            status="error",   
            message="An unexpected error occurred"  
        ), 500  
