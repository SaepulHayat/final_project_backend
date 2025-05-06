from flask import Blueprint
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.user_service import UserService

user_bp = Blueprint('user', __name__)
user_service = UserService()

@user_bp.route('/referral', methods=['GET'])
@jwt_required()
def get_referral_info():
    """Get user referral information."""
    user_id = get_jwt_identity()
    return user_service.get_referral_info(user_id)

@user_bp.route('/balance', methods=['GET'])
@jwt_required()
def get_balance():
    """Get user balance."""
    user_id = get_jwt_identity()
    return user_service.get_balance(user_id)
