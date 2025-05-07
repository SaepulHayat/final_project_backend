from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..services.book_service import BookService
from ..utils.response import create_response
from ..utils.decorators import role_required
from ..utils.roles import UserRoles

book_bp = Blueprint('books', __name__, url_prefix='/api/v1/books')
book_service = BookService()

# CREATE BOOK
@book_bp.route('/', methods=['POST'])
@role_required([UserRoles.SELLER.value, UserRoles.ADMIN.value])
def create_book_route():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    result = book_service.create_book(data, user_id)
    return create_response(**result), result.get("status_code", 500)

# GET ALL BOOKS
@book_bp.route('/', methods=['GET'])
def get_books_route():
    args = request.args
    result = book_service.get_all_books(args)
    return create_response(**result), result.get("status_code", 500)

# GET BOOK BY ID
@book_bp.route('/<int:book_id>', methods=['GET'])
def get_book_by_id_route(book_id):
    result = book_service.get_book_by_id(book_id)
    return create_response(**result), result.get("status_code", 500)

# GET CURRENT USER'S BOOKS
@book_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_books_route():
    user_id = get_jwt_identity()
    args = request.args
    result = book_service.get_books_by_user(user_id, args)
    return create_response(**result), result.get("status_code", 500)

# UPDATE BOOK
@book_bp.route('/<int:book_id>', methods=['PATCH', 'PUT'])
@jwt_required()
def update_book_route(book_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    result = book_service.update_book(book_id, data, user_id)
    return create_response(**result), result.get("status_code", 500)

# DELETE BOOK
@book_bp.route('/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book_route(book_id):
    user_id = get_jwt_identity()
    result = book_service.delete_book(book_id, user_id)
    return create_response(**result), result.get("status_code", 500)
