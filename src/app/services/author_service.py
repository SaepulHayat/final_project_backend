from ..model.author import Author
from ..extensions import db
from ..utils.validators import validate_author_input
from ..utils.response import success_response, error_response # Or handle errors via exceptions
from sqlalchemy import func # Import func for case-insensitive comparison
import logging

logger = logging.getLogger(__name__)

class AuthorService:
    def create_author(self, data):
        errors = validate_author_input(data)
        if errors:
            # Option 1: Return error dict (as used in auth_service)
            return error_response("Validation failed", errors=errors)
            # Option 2: Raise a custom validation exception
            # raise ValidationException("Validation failed", errors=errors)

        # Check for name uniqueness (case-insensitive)
        full_name = data.get('full_name')
        existing_author = Author.query.filter(
            func.lower(Author.full_name) == func.lower(full_name)
        ).first()
        if existing_author:
            return error_response("Author with this name already exists",
error="duplicate_name")

        new_author = Author(
            full_name=full_name,
            bio=data.get('bio')
        )
        try:
            db.session.add(new_author)
            db.session.commit()
            # Return success with author data, excluding sensitive info if any
            return success_response("Author created successfully",
data=new_author.to_dict()) # Assuming a to_dict() method
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating author: {e}", exc_info=True)
            return error_response("Failed to create author", error=str(e))

    def get_all_authors(self, args):
        # Implement pagination, filtering (e.g., by name), searching
        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)
        search_term = args.get('search')

        query = Author.query

        if search_term:
            # Search across full_name (case-insensitive)
            query = query.filter(Author.full_name.ilike(f'%{search_term}%'))

        paginated_authors = query.paginate(page=page, per_page=per_page,
error_out=False)

        return success_response(
            "Authors retrieved successfully",
            data={
                "authors": [author.to_dict() for author in paginated_authors.items],
                "total": paginated_authors.total,
                "pages": paginated_authors.pages,
                "current_page": paginated_authors.page
            }
        )

    def get_author_by_id(self, author_id):
        author = Author.query.get(author_id)
        if not author:
            return error_response("Author not found", error="not_found")
        return success_response("Author found", data=author.to_dict())

    def get_books_by_author(self, author_id, args):
        author = Author.query.get(author_id)
        if not author:
            return error_response("Author not found", error="not_found")

        # Implement pagination for books if needed
        # For now, return all books associated with the author
        books = [book.to_simple_dict() for book in author.books.all()] # Use .all() to execute the dynamic query
        return success_response("Books by author retrieved", data={"books": books})


    def update_author(self, author_id, data):
        author = Author.query.get(author_id)
        if not author:
            return error_response("Author not found", error="not_found")

        errors = validate_author_input(data, is_update=True) # Allow partial updates
        if errors:

            return error_response("Validation failed", errors=errors)

        # Check for name uniqueness if full_name is being updated
        if 'full_name' in data and data['full_name'].lower() != author.full_name.lower():
            existing_author = Author.query.filter(
                func.lower(Author.full_name) == func.lower(data['full_name']),
                Author.id != author_id # Exclude the current author
            ).first()
            if existing_author:
                return error_response("Another author with this name already exists",
error="duplicate_name")
            author.full_name = data['full_name'] # Update only if validation passes

        # Update other fields if provided in data
        if 'bio' in data:
            author.bio = data['bio']

        try:
            db.session.commit()
            return success_response("Author updated successfully", data=author.to_dict())
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating author {author_id}: {e}", exc_info=True)
            return error_response("Failed to update author", error=str(e))

    def delete_author(self, author_id):
        author = Author.query.get(author_id)
        if not author:
            return error_response("Author not found", error="not_found")

        # **Relationship Handling:** Check if deletion is allowed based on relationships
        # Example: If books are associated and cascade isn't set to delete them
        # Because lazy='dynamic', author.books is a query object. Execute it.
        if author.books.first():
            return error_response("Cannot delete author with associated books",
error="conflict")

        try:
            db.session.delete(author)
            db.session.commit()
            return success_response("Author deleted successfully")
        except Exception as e: # Catch potential IntegrityError if DB prevents deletion
            db.session.rollback()

            logger.error(f"Error deleting author {author_id}: {e}", exc_info=True)
            # Check if it's a foreign key constraint violation (requires importing sqlalchemy)
            # import sqlalchemy
            # if isinstance(e, sqlalchemy.exc.IntegrityError):
            #    return error_response("Cannot delete author due to existing references (e.g.,
# books)", error="conflict")
            return error_response("Failed to delete author", error=str(e))