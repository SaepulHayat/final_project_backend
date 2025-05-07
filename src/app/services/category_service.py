from ..model.category import Category
from ..model.book import Book # Needed for querying books by category
from ..extensions import db
from ..utils.validators import validate_category_input
from ..utils.response import success_response, error_response # Or handle errors via exceptions
from sqlalchemy import func # For case-insensitive checks
from sqlalchemy.exc import IntegrityError # To catch unique constraint violations
import logging

logger = logging.getLogger(__name__)

class CategoryService:

    def create_category(self, data):
        errors = validate_category_input(data)
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        # Strip whitespace and apply title case
        name_input = data.get('name', "").strip()
        if not name_input: # Re-check after stripping if name was just whitespace
            return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)
        name = name_input.title() # Capitalize first letter of each word

        # Check for name uniqueness (case-insensitive comparison)
        existing_category = Category.query.filter(func.lower(Category.name) == func.lower(name)).first()
        if existing_category:
            # Return conflict even if casing is different, as we store title-cased
            return error_response(f"Category '{name}' already exists", error="duplicate_name", status_code=409) # 409 Conflict

        new_category = Category(name=name) # Store the title-cased name
        try:
            db.session.add(new_category)
            db.session.commit()
            logger.info(f"Category created: ID {new_category.id}, Name '{new_category.name}'")
            # Use the to_dict() method from the model for the response data
            return success_response("Category created successfully", data=new_category.to_dict(), status_code=201)
        except IntegrityError as e: # Catch potential race condition duplicate
            db.session.rollback()
            logger.warning(f"Integrity error creating category '{name}': {e}")
            return error_response(f"Category '{name}' already exists", error="duplicate_name", status_code=409)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating category '{name}': {e}", exc_info=True)
            return error_response("Failed to create category", error=str(e), status_code=500)

    def get_all_categories(self, args):
        # Implement pagination, filtering (e.g., by name), searching
        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)
        search_term = args.get('search')
        query = Category.query.order_by(Category.name) # Order alphabetically

        if search_term:
            query = query.filter(Category.name.ilike(f'%{search_term}%'))

        try:
            paginated_categories = query.paginate(page=page, per_page=per_page, error_out=False)
            return success_response(
                "Categories retrieved successfully",
                data={
                    # Use the to_dict() method from the model for each category
                    "categories": [cat.to_dict() for cat in paginated_categories.items],
                    "total": paginated_categories.total,
                    "pages": paginated_categories.pages,
                    "current_page": paginated_categories.page
                },
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error retrieving categories: {e}", exc_info=True)
            return error_response("Failed to retrieve categories", error=str(e), status_code=500)

    def get_category_by_id(self, category_id):
        category = Category.query.get(category_id)
        if not category:
            return error_response("Category not found", error="not_found", status_code=404)
        # Use the to_dict() method from the model for the response data
        return success_response("Category found", data=category.to_dict(), status_code=200)

    def get_books_by_category(self, category_id, args):
        category = Category.query.get(category_id)
        if not category:
            return error_response("Category not found", error="not_found", status_code=404)

        # Implement pagination for books within the category
        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)

        try:
            # Access books through the relationship and paginate
            # Ensure Book model has a to_simple_dict() method
            paginated_books = Book.query.with_parent(category).paginate(page=page, per_page=per_page, error_out=False)
            return success_response(
                f"Books in category '{category.name}' retrieved successfully",
                data={
                    # Use Book's to_simple_dict()
                    "books": [book.to_simple_dict() for book in paginated_books.items],
                    "total": paginated_books.total,
                    "pages": paginated_books.pages,
                    "current_page": paginated_books.page,
                    "category": category.to_simple_dict()
                },
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error retrieving books for category {category_id}: {e}", exc_info=True)
            return error_response("Failed to retrieve books for category", error=str(e), status_code=500)

    def update_category(self, category_id, data):
        category = Category.query.get(category_id)
        if not category:
            return error_response("Category not found", error="not_found", status_code=404)

        errors = validate_category_input(data, is_update=True) # Allow partial updates
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        updated = False
        new_name_title_cased = None # Variable to hold the potential new name
        if 'name' in data:
            name_input = data['name'].strip()
            if not name_input: # Check if name is empty after stripping
                return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)

            new_name_title_cased = name_input.title() # Apply title case

            # Check if name actually changed (case-insensitive comparison with original)
            # and also compare title-cased new name with current name
            if new_name_title_cased.lower() != category.name.lower():
                # Check if the *new* title-cased name already exists (excluding the current category)
                existing_category = Category.query.filter(
                    func.lower(Category.name) == func.lower(new_name_title_cased),
                    Category.id != category_id
                ).first()
                if existing_category:
                    return error_response(f"Another category with the name '{new_name_title_cased}' already exists", error="duplicate_name", status_code=409)
                category.name = new_name_title_cased # Update with title-cased name
                updated = True
            elif new_name_title_cased != category.name:
                # Handles case where only casing changes e.g. "sci fi" -> "Sci Fi" but lower is same
                category.name = new_name_title_cased
                updated = True

        if not updated:
            # If name was provided but resulted in no change (same name, same case)
            if 'name' in data:
                return error_response("Provided name is the same as the current name", error="no_change", status_code=400)
            else:
                # If 'name' was not in data dictionary at all
                return error_response("No update data provided", error="no_change", status_code=400)

        try:
            db.session.commit()
            logger.info(f"Category updated: ID {category.id}, New Name '{category.name}'")
            # Use the to_dict() method from the model for the response data
            return success_response("Category updated successfully", data=category.to_dict(), status_code=200)
        except IntegrityError as e: # Catch potential race condition duplicate
            db.session.rollback()
            logger.warning(f"Integrity error updating category {category_id} to '{new_name_title_cased}': {e}")
            # Use the name variable that caused the error
            return error_response(f"Another category with the name '{new_name_title_cased}' already exists", error="duplicate_name", status_code=409)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating category {category_id}: {e}", exc_info=True)
            return error_response("Failed to update category", error=str(e), status_code=500)

    def delete_category(self, category_id):
        category = Category.query.get(category_id)
        if not category:
            return error_response("Category not found", error="not_found", status_code=404)

        try:
            category_name = category.name # Store name for logging before deletion
            db.session.delete(category)
            db.session.commit()
            logger.info(f"Category deleted: ID {category_id}, Name '{category_name}'")
            # Return 204 No Content status code via the route handler
            return success_response("Category deleted successfully", status_code=200) # Route will change to 204
        except Exception as e: # Catch potential DB errors
            db.session.rollback()
            logger.error(f"Error deleting category {category_id}: {e}", exc_info=True)
            return error_response("Failed to delete category", error=str(e), status_code=500)