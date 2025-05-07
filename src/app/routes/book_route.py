from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from ..services.book_service import BookService
from ..utils.response import create_response
from ..utils.decorators import role_required
from ..utils.roles import UserRoles
import logging

logger = logging.getLogger(__name__)
book_bp = Blueprint('books', __name__, url_prefix='/api/v1/books')
book_service = BookService()

@book_bp.route('/', methods=['POST'])
@role_required([UserRoles.SELLER.value])
def create_book_route():
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data: return create_response(status="error", message="Request body must be JSON"), 400
    result = book_service.create_book(data, user_id)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code


@book_bp.route('/', methods=['GET'])
def get_books_route():
    args = request.args
    # Import Location, City, State, Country if not already for eager loading path
    # from ..model.location import Location
    # from ..model.city import City
    # from ..model.state import State
    # from ..model.country import Country
    result = book_service.get_all_books(args)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@book_bp.route('/<int:book_id>', methods=['GET'])
def get_book_by_id_route(book_id):
    # Import Location, City, State, Country if not already for eager loading path
    result = book_service.get_book_by_id(book_id)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@book_bp.route('/me', methods=['GET'])
@jwt_required()
def get_my_books_route():
    user_id = get_jwt_identity()
    args = request.args
    result = book_service.get_books_by_user(user_id, args)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@book_bp.route('/<int:book_id>', methods=['PATCH', 'PUT'])
@jwt_required()
def update_book_route(book_id):
    user_id = get_jwt_identity()
    data = request.get_json()
    if not data: return create_response(status="error", message="Request body must be JSON"), 400
    result = book_service.update_book(book_id, data, user_id)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@book_bp.route('/<int:book_id>', methods=['DELETE'])
@jwt_required()
def delete_book_route(book_id):

    user_id = get_jwt_identity()
    result = book_service.delete_book(book_id, user_id)
    status_code = result.get('status_code', 500)
    if result.get('status') == 'success' and (status_code == 200 or status_code == 204):
        return create_response(**result), status_code # Or return '', 204 for explicit 204
    return create_response(**result), status_code
