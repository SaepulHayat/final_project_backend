from flask import Blueprint, request, jsonify
from ..services.author_service import AuthorService
from ..utils.response import create_response
from ..utils.decorators import role_required
from ..utils.roles import UserRoles
from flask_jwt_extended import jwt_required
import logging

logger = logging.getLogger(__name__)
author_bp = Blueprint('authors', __name__, url_prefix='/api/v1/authors')
author_service = AuthorService()

@author_bp.route('/', methods=['POST'])
@role_required([UserRoles.SELLER.value]) # Example role check
def create_author_route():
    data = request.get_json()
    if not data:
        return create_response("error", "Request body must be JSON"), 400

    result = author_service.create_author(data)
    status_code = 201 if result.get('status') == 'success' else 400 # Or determine based
# on error type
    if result.get('error') == 'duplicate_name':
        status_code = 409 # Conflict for duplicate name
    return create_response(**result), status_code # Unpack dict into create_response


@author_bp.route('/', methods=['GET'])
def get_authors_route():
    args = request.args # For pagination/filtering/searching
    result = author_service.get_all_authors(args)
    # Public endpoint, usually success unless server error
    status_code = 200 if result.get('status') == 'success' else 500
    return create_response(**result), status_code

@author_bp.route('/<int:author_id>', methods=['GET'])
def get_author_by_id_route(author_id):
    result = author_service.get_author_by_id(author_id)
    status_code = 200
    if result.get('status') == 'error':
        status_code = 404 if result.get('error') == 'not_found' else 500
    return create_response(**result), status_code

@author_bp.route('/<int:author_id>/books', methods=['GET'])
def get_books_by_author_route(author_id):
    args = request.args
    result = author_service.get_books_by_author(author_id, args)
    status_code = 200
    if result.get('status') == 'error':
        status_code = 404 if result.get('error') == 'not_found' else 500
    return create_response(**result), status_code


@author_bp.route('/<int:author_id>', methods=['PATCH']) # Changed PUT to PATCH for
# partial updates
@role_required([UserRoles.SELLER.value])
@role_required([UserRoles.SELLER.value])
def update_author_route(author_id):
    data = request.get_json()
    if not data:
        return create_response("error", "Request body must be JSON"), 400

    result = author_service.update_author(author_id, data)
    status_code = 200
    if result.get('status') == 'error':
        if result.get('error') == 'not_found':
            status_code = 404
        elif 'Validation failed' in result.get('message', ''):
            status_code = 400

        elif result.get('error') == 'duplicate_name':
            status_code = 409 # Conflict for duplicate name
        else:
            status_code = 500 # Or specific code based on error
    return create_response(**result), status_code

@author_bp.route('/<int:author_id>', methods=['DELETE'])
@role_required([UserRoles.SELLER.value])
@role_required([UserRoles.SELLER.value])
def delete_author_route(author_id):
    result = author_service.delete_author(author_id)
    status_code = 200 # Or 204 No Content on successful delete
    if result.get('status') == 'error':
        if result.get('error') == 'not_found':
            status_code = 404
        elif result.get('error') == 'conflict':
            status_code = 409 # Conflict if deletion is blocked
        else:
            status_code = 500
    return create_response(**result), status_code

# Register blueprint in app factory (e.g., in app/__init__.py)
# from .routes.author_route import author_bp
# app.register_blueprint(author_bp)