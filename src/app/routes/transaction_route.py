# route/transaction_route.py
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.transaction_service import TransactionService
from ..utils.response import create_response, error_response, success_response
from ..model.user import User
from ..utils.roles import UserRoles
import logging

logger = logging.getLogger(__name__)
transaction_bp = Blueprint('transaction', __name__)
transaction_service = TransactionService()

@transaction_bp.route('/', methods=['POST'])
@jwt_required()
def create_transaction():
    try:
        data = request.get_json(silent=True) or request.form
        customer_id = get_jwt_identity()
        
        
        # Validasi role customer
        user = User.query.get(customer_id)
        logger.info(f"User role: '{user.role}', UserRoles.CUSTOMER.value: '{UserRoles.CUSTOMER.value}'")
        if user.role != UserRoles.CUSTOMER.value:
            
            return error_response("Only customers can create transactions"), 403
        
        result = transaction_service.create_transaction(data, customer_id)
        
        if result.get('status') == 'success':
            return jsonify(result), 201
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Create transaction error: {str(e)}", exc_info=True)
        return error_response("Internal server error"), 500

@transaction_bp.route('/<int:transaction_id>', methods=['GET'])
@jwt_required()
def get_transaction(transaction_id):
    try:
        user_id = get_jwt_identity()
        result = transaction_service.get_transaction(transaction_id, user_id)
        
        if result.get('status') == 'success':
            return jsonify(result), 200
        else:
            status_code = 404 if "not found" in result.get('message', '').lower() else 400
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f"Get transaction error: {str(e)}", exc_info=True)
        return error_response("Internal server error"), 500

@transaction_bp.route('/<int:transaction_id>/status', methods=['PUT'])
@jwt_required()
def update_transaction_status(transaction_id):
    try:
        data = request.get_json(silent=True) or request.form
        user_id = get_jwt_identity()
        new_status = data.get('status')
        
        if not new_status:
            return error_response("Status is required"), 400
            
        result = transaction_service.update_transaction_status(transaction_id, new_status, user_id)
        
        if result.get('status') == 'success':
            return jsonify(result), 200
        else:
            status_code = 403 if "unauthorized" in result.get('message', '').lower() else 400
            return jsonify(result), status_code
            
    except Exception as e:
        logger.error(f"Update transaction error: {str(e)}", exc_info=True)
        return error_response("Internal server error"), 500

@transaction_bp.route('/customer', methods=['GET'])
@jwt_required()
def get_customer_transactions():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != UserRoles.CUSTOMER.value:
            return error_response("Unauthorized access"), 403
        
        status = request.args.get('status')
            
        result = transaction_service.get_user_transactions(user_id, UserRoles.CUSTOMER.value, status)
        
        if result.get('status') == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Get customer transactions error: {str(e)}", exc_info=True)
        return error_response("Internal server error"), 500


@transaction_bp.route('/seller', methods=['GET'])
@jwt_required()
def get_seller_transactions():
    try:
        user_id = get_jwt_identity()
        user = User.query.get(user_id)
        
        if user.role != UserRoles.SELLER.value:
            return error_response("Unauthorized access"), 403
            
        result = transaction_service.get_user_transactions(user_id, UserRoles.SELLER)
        
        if result.get('status') == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 400
            
    except Exception as e:
        logger.error(f"Get seller transactions error: {str(e)}", exc_info=True)
        return error_response("Internal server error"), 500
