from flask import Blueprint, request
from ..services.category_service import CategoryService
from ..utils.response import create_response
from ..utils.decorators import role_required
from ..utils.roles import UserRoles
import logging

logger = logging.getLogger(__name__)

category_bp = Blueprint("categories", __name__, url_prefix="/api/v1/categories")
category_service = CategoryService()


@category_bp.route("/", methods=["POST"])
@role_required([UserRoles.ADMIN.value])
def create_category():
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    result = category_service.create_category(data)
    return create_response(**result), result.get("status_code", 500)


@category_bp.route("/", methods=["GET"])
def get_all_categories():
    result = category_service.get_all_categories(request.args)
    return create_response(**result), result.get("status_code", 500)


@category_bp.route("/<int:category_id>", methods=["GET"])
def get_category_by_id(category_id):
    result = category_service.get_category_by_id(category_id)
    return create_response(**result), result.get("status_code", 500)


@category_bp.route("/<int:category_id>/books", methods=["GET"])
def get_books_by_category(category_id):
    result = category_service.get_books_by_category(category_id, request.args)
    return create_response(**result), result.get("status_code", 500)

@category_bp.route("/<int:category_id>", methods=["PATCH", "PUT"])
@role_required([UserRoles.ADMIN.value])
def update_category(category_id):
    data = request.get_json()
    if not data:
        return create_response(status="error", message="Request body must be JSON"), 400

    result = category_service.update_category(category_id, data)
    return create_response(**result), result.get("status_code", 500)


@category_bp.route("/<int:category_id>", methods=["DELETE"])
@role_required([UserRoles.ADMIN.value])
def delete_category(category_id):
    result = category_service.delete_category(category_id)
    status_code = result.get("status_code", 500)
    return ("", 204) if result.get("status") == "success" and status_code == 200 else (create_response(**result), status_code)