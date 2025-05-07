from functools import wraps
from typing import Callable, List, Any
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity, get_jwt
from ..model.user import User
from ..utils.roles import UserRoles
import logging

logger = logging.getLogger(__name__)

def role_required(allowed_roles: List[str]):
    def decorator(fn: Callable[..., Any]):
        @wraps(fn)
        def wrapper(*args: Any, **kwargs: Any):
            try:
                # Verify JWT
                verify_jwt_in_request()
                jwt_data = get_jwt()
                current_user_id = get_jwt_identity()

                # Get user from DB
                user = User.query.get(current_user_id)
                if not user:
                    return jsonify({
                        "status": "error",
                        "message": "User not found"
                    }), 404

                # Check role (case-insensitive)
                user_role = user.role.lower()
                normalized_allowed_roles = [r.lower() for r in allowed_roles]

                if user_role not in normalized_allowed_roles:
                    logger.warning(
                        f"Unauthorized access attempt by user_id={current_user_id}, role={user_role}. "
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

# Shortcut Decorators
seller_required = role_required([UserRoles.SELLER.value])
customer_required = role_required([UserRoles.CUSTOMER.value])
admin_required = role_required([UserRoles.ADMIN.value])
