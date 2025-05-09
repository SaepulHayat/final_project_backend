from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.wishlist_service import WishlistService
from ..utils.response import create_response, error_response, success_response
import logging

logger = logging.getLogger(__name__)
wishlist_bp = Blueprint('wishlist', __name__)
wishlist_service = WishlistService()

@wishlist_bp.route('/', methods=['POST'])
@jwt_required()
def add_to_wishlist():
    """Add a book to user's wishlist."""
    try:
        user_id = get_jwt_identity()
        data = request.get_json(silent=True)
        
        if not data:
            return create_response(status="error", message="Request body must be JSON"), 400
            
        if 'book_id' not in data:
            return create_response(status="error", message="Book ID is required"), 400
            
        result = wishlist_service.add_to_wishlist(user_id, data['book_id'])
        status_code = result.get('status_code', 500)
        return create_response(**result), status_code
        
    except Exception as e:
        logger.error(f"Unexpected error in add_to_wishlist: {e}", exc_info=True)
        return create_response(status="error", message="An unexpected error occurred"), 500

@wishlist_bp.route('/', methods=['GET'])
@jwt_required()
def get_wishlist():
    """Get user's wishlist."""
    try:
        user_id = get_jwt_identity()
        result = wishlist_service.get_user_wishlist(user_id)
        status_code = result.get('status_code', 500)
        return create_response(**result), status_code
        
    except Exception as e:
        logger.error(f"Unexpected error in get_wishlist: {e}", exc_info=True)
        return create_response(status="error", message="An unexpected error occurred"), 500

@wishlist_bp.route('/<int:wishlist_id>', methods=['DELETE'])
@jwt_required()
def remove_from_wishlist(wishlist_id):
    """Remove a book from user's wishlist."""
    try:
        user_id = get_jwt_identity()
        result = wishlist_service.remove_from_wishlist(wishlist_id, user_id)
        status_code = result.get('status_code', 500)
        return create_response(**result), status_code
        
    except Exception as e:
        logger.error(f"Unexpected error in remove_from_wishlist: {e}", exc_info=True)
        return create_response(status="error", message="An unexpected error occurred"), 500
