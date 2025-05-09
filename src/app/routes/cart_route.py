from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.cart_service import CartService
from ..utils.response import create_response, error_response, success_response
import logging

logger = logging.getLogger(__name__)
cart_bp = Blueprint('cart', __name__)
cart_service = CartService()

@cart_bp.route('/', methods=['POST'])
@jwt_required()
def add_to_cart():
    """Add a book to user's cart."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json(silent=True)
        
        if not data:
            return create_response(status="error", message="Request body must be JSON"), 400
            
        if 'book_id' not in data:
            return create_response(status="error", message="Book ID is required"), 400
            
        quantity = data.get('quantity', 1)
        
        result = cart_service.add_to_cart(user_id, data['book_id'], quantity)
        status_code = result.get('status_code', 500)
        return create_response(**result), status_code
        
    except Exception as e:
        logger.error(f"Unexpected error in add_to_cart: {e}", exc_info=True)
        return create_response(status="error", message="An unexpected error occurred"), 500

@cart_bp.route('/', methods=['GET'])
@jwt_required()
def get_cart():
    """Get user's cart."""
    try:
        user_id = get_jwt_identity()
        result = cart_service.get_user_cart(user_id)
        status_code = result.get('status_code', 500)
        return create_response(**result), status_code
        
    except Exception as e:
        logger.error(f"Unexpected error in get_cart: {e}", exc_info=True)
        return create_response(status="error", message="An unexpected error occurred"), 500

@cart_bp.route('/<int:cart_id>', methods=['PUT'])
@jwt_required()
def update_cart(cart_id):
    """Update quantity of a book in user's cart."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json(silent=True)
        
        if not data:
            return create_response(status="error", message="Request body must be JSON"), 400
            
        if 'quantity' not in data:
            return create_response(status="error", message="Quantity is required"), 400
            
        result = cart_service.update_cart_quantity(cart_id, user_id, data['quantity'])
        status_code = result.get('status_code', 500)
        return create_response(**result), status_code
        
    except Exception as e:
        logger.error(f"Unexpected error in update_cart: {e}", exc_info=True)
        return create_response(status="error", message="An unexpected error occurred"), 500

@cart_bp.route('/<int:cart_id>', methods=['DELETE'])
@jwt_required()
def remove_from_cart(cart_id):
    """Remove a book from user's cart."""
    try:
        user_id = get_jwt_identity()
        result = cart_service.remove_from_cart(cart_id, user_id)
        status_code = result.get('status_code', 500)
        return create_response(**result), status_code
        
    except Exception as e:
        logger.error(f"Unexpected error in remove_from_cart: {e}", exc_info=True)
        return create_response(status="error", message="An unexpected error occurred"), 500

@cart_bp.route('/', methods=['DELETE'])
@jwt_required()
def clear_cart():
    """Clear user's cart."""
    try:
        user_id = get_jwt_identity()
        result = cart_service.clear_cart(user_id)
        status_code = result.get('status_code', 500)
        return create_response(**result), status_code
        
    except Exception as e:
        logger.error(f"Unexpected error in clear_cart: {e}", exc_info=True)
        return create_response(status="error", message="An unexpected error occurred"), 500
