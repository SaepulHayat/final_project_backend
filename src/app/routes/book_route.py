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
    categories = request.args.get('categories')
    publisher_name = request.args.get('publisher_name')
    author_name = request.args.get('author_name')
    seller_name = request.args.get('seller_name')
    city_name = request.args.get('city_name')
    min_rating = request.args.get('min_rating', type=float)
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)

    result = book_service.get_all_books_filtered(
        request.args, # Pass the full request.args dictionary
        categories=categories,
        publisher_name=publisher_name,
        author_name=author_name,
        seller_name=seller_name,
        city_name=city_name,
        min_rating=min_rating,
        min_price=min_price,
        max_price=max_price
    )
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@book_bp.route('/<int:book_id>', methods=['GET'])
def get_book_by_id_route(book_id):
    result = book_service.get_book_by_id(book_id)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@book_bp.route('/me', methods=['GET'])
@role_required([UserRoles.SELLER.value])
def get_my_books_route():
    user_id = get_jwt_identity()
    args = request.args
    result = book_service.get_books_by_user(user_id, args)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@book_bp.route('/<int:book_id>', methods=['PATCH', 'PUT'])
@role_required([UserRoles.SELLER.value])
def update_book_route(book_id):
    user_id = int(get_jwt_identity())
    data = request.get_json()
    if not data: return create_response(status="error", message="Request body must be JSON"), 400
    result = book_service.update_book(book_id, data, user_id)
    status_code = result.get('status_code', 500)
    return create_response(**result), status_code

@book_bp.route('/<int:book_id>', methods=['DELETE'])
@role_required([UserRoles.SELLER.value])
def delete_book_route(book_id):

    user_id = int(get_jwt_identity()) # Cast to int
    result = book_service.delete_book(book_id, user_id)
    status_code = result.get('status_code', 500)
    if result.get('status') == 'success' and (status_code == 200 or status_code == 204):
        return create_response(**result), status_code # Or return '', 204 for explicit 204
    return create_response(**result), status_code
