from functools import wraps
from typing import Callable, List, Any
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from src.app.model.user import User
from src.app.utils.roles import UserRoles
from src.app.model.blacklist_token import BlacklistToken
import logging

logger = logging.getLogger(__name__)

def role_required(allowed_roles: List[str]):
    """Decorator generik untuk role-based access control (RBAC)"""
    def decorator(fn: Callable[..., Any]):
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            try:
                # Verify JWT dan cek blacklist
                verify_jwt_in_request()
                jwt_data = get_jwt()
                if BlacklistToken.is_token_revoked(jwt_data["jti"]):
                    return jsonify({"message": "Token revoked"}), 401

                # Dapatkan user dari cache jika memungkinkan
                current_user_id = get_jwt_identity()
                user = User.get_cached(current_user_id)  # Implement cached method
                
                # Authorization check
                if not user or user.role not in allowed_roles:
                    logger.warning(
                        f"Unauthorized access attempt by {current_user_id}. "
                        f"Allowed roles: {allowed_roles}"
                    )
                    return jsonify({
                        "status": "error",
                        "message": "Insufficient permissions",
                        "allowed_roles": allowed_roles
                    }), 403
                
                return fn(*args, **kwargs)
            
            except Exception as e:
                logger.error(f"Auth error: {str(e)}", exc_info=True)
                return jsonify({
                    "status": "error",
                    "message": "Authentication failed"
                }), 401
        return wrapper
    return decorator

# Contoh implementasi spesifik
seller_required = role_required([UserRoles.SELLER.value])
customer_required = role_required([UserRoles.CUSTOMER.value])
# admin_required = role_required([UserRoles.ADMIN.value])
