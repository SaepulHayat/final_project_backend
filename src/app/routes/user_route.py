from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.user_service import UserService
from ..utils.roles import UserRoles

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

@user_bp.route('/', methods=['GET'])
@jwt_required()
def get_all_users():
    return user_service.get_all_users()

@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_profile():
    user_id = get_jwt_identity()
    return user_service.get_user_by_id(user_id)

@user_bp.route('/me', methods=['PUT'])
@jwt_required()
def update_my_profile():
    user_id = get_jwt_identity()
    data = request.get_json()
    return user_service.update_user(user_id, data)

@user_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    jwt_data = get_jwt()
    if jwt_data.get("role") != UserRoles.SELLER.value:
        return jsonify({"status": "error", "message": "Unauthorized"}), 403
    return user_service.delete_user_by_id(user_id)
