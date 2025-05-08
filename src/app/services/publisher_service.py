from ..model.publisher import Publisher
from ..model.book import Book # Needed for querying books by publisher and handling deletion
from ..extensions import db
from ..utils.validators import validate_publisher_input
from ..utils.response import success_response, error_response # Or handle errors via exceptions
from sqlalchemy import func # For case-insensitive checks
from sqlalchemy.exc import IntegrityError # To catch unique constraint violations
import logging

logger = logging.getLogger(__name__)

class PublisherService:
    def create_publisher(self, data):
        errors = validate_publisher_input(data)
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        name_input = data.get('name', '').strip()
        if not name_input: # Re-check after stripping
            return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)

        # Check for name uniqueness (case-insensitive comparison)
        existing_publisher = Publisher.query.filter(func.lower(Publisher.name) == func.lower(name_input)).first()
        if existing_publisher:
            return error_response(f"Publisher '{name_input}' already exists", error="duplicate_name", status_code=409) # 409 Conflict

        new_publisher = Publisher(name=name_input) # Store the name as provided (trimmed)
        try:
            db.session.add(new_publisher)
            db.session.commit()
            logger.info(f"Publisher created: ID {new_publisher.id}, Name '{new_publisher.name}'")
            return success_response("Publisher created successfully", data=new_publisher.to_dict(), status_code=201)
        except IntegrityError as e: # Catch potential race condition duplicate
            db.session.rollback()
            logger.warning(f"Integrity error creating publisher '{name_input}': {e}")
            return error_response(f"Publisher '{name_input}' already exists", error="duplicate_name", status_code=409)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating publisher '{name_input}': {e}", exc_info=True)
            return error_response("Failed to create publisher", error=str(e), status_code=500)

    def get_all_publishers(self, args):
        # Implement pagination, filtering (e.g., by name), searching
        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)
        search_term = args.get('search')

        query = Publisher.query.order_by(Publisher.name) # Order alphabetically
        if search_term:
            query = query.filter(Publisher.name.ilike(f'%{search_term}%'))

        try:
            paginated_publishers = query.paginate(page=page, per_page=per_page, error_out=False)
            return success_response(
                "Publishers retrieved successfully",
                data={
                    # Use simple dict for lists
                    "publishers": [pub.to_simple_dict() for pub in paginated_publishers.items],
                    "total": paginated_publishers.total,
                    "pages": paginated_publishers.pages,
                    "current_page": paginated_publishers.page
                },
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error retrieving publishers: {e}", exc_info=True)
            return error_response("Failed to retrieve publishers", error=str(e), status_code=500)

    def get_publisher_by_id(self, publisher_id):
        publisher = Publisher.query.get(publisher_id)
        if not publisher:
            return error_response("Publisher not found", error="not_found", status_code=404)
        # Use full dict for single item view
        return success_response("Publisher found", data=publisher.to_dict(), status_code=200)

    def get_books_by_publisher(self, publisher_id, args):
        publisher = Publisher.query.get(publisher_id)
        if not publisher:
            return error_response("Publisher not found", error="not_found", status_code=404)

        # Implement pagination for books within the publisher
        page = args.get('page', 1, type=int)
        per_page = args.get('per_page', 10, type=int)

        try:
            # Access books through the relationship and paginate
            # Ensure Book model has a to_simple_dict() method
            paginated_books = Book.query.with_parent(publisher).paginate(page=page, per_page=per_page, error_out=False)

            return success_response(
                f"Books by publisher '{publisher.name}' retrieved successfully",
                data={
                    "books": [book.to_simple_dict() for book in paginated_books.items], # Use simple book representation
                    "total": paginated_books.total,
                    "pages": paginated_books.pages,
                    "current_page": paginated_books.page,
                    "publisher": publisher.to_simple_dict() # Include publisher info
                },
                status_code=200
            )
        except Exception as e:
            logger.error(f"Error retrieving books for publisher {publisher_id}: {e}", exc_info=True)
            return error_response("Failed to retrieve books for publisher", error=str(e), status_code=500)

    def update_publisher(self, publisher_id, data):
        publisher = Publisher.query.get(publisher_id)
        if not publisher:
            return error_response("Publisher not found", error="not_found", status_code=404)

        errors = validate_publisher_input(data, is_update=True) # Allow partial updates
        if errors:
            return error_response("Validation failed", errors=errors, status_code=400)

        updated = False
        new_name_input = None
        if 'name' in data:
            name_input = data['name'].strip()
            if not name_input: # Check if name is empty after stripping
                return error_response("Validation failed", errors={'name': 'Name cannot be empty'}, status_code=400)

            new_name_input = name_input # Keep track of the proposed new name

            # Check if name actually changed (case-insensitive comparison with original)
            if new_name_input.lower() != publisher.name.lower():
                # Check if the *new* name already exists (excluding the current publisher)
                existing_publisher = Publisher.query.filter(
                    func.lower(Publisher.name) == func.lower(new_name_input),
                    Publisher.id != publisher_id
                ).first()
                if existing_publisher:
                    return error_response(f"Another publisher with the name '{new_name_input}' already exists", error="duplicate_name", status_code=409)

                publisher.name = new_name_input # Update with new name
                updated = True
            elif new_name_input != publisher.name:
                # Handles case where only casing changes but lower is same, still update
                publisher.name = new_name_input
                updated = True


        if not updated:
            # If name was provided but resulted in no change
            if 'name' in data:
                return error_response("Provided name is the same as the current name", error="no_change", status_code=400)
            else:
                # If 'name' was not in data dictionary at all
                return error_response("No update data provided", error="no_change", status_code=400)


        try:
            db.session.commit()
            logger.info(f"Publisher updated: ID {publisher.id}, New Name '{publisher.name}'")
            return success_response("Publisher updated successfully", data=publisher.to_dict(), status_code=200)
        except IntegrityError as e: # Catch potential race condition duplicate
            db.session.rollback()
            logger.warning(f"Integrity error updating publisher {publisher_id} to '{new_name_input}': {e}")
            # Use the name variable that caused the error
            return error_response(f"Another publisher with the name '{new_name_input}' already exists", error="duplicate_name", status_code=409)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating publisher {publisher_id}: {e}", exc_info=True)
            return error_response("Failed to update publisher", error=str(e), status_code=500)

    def delete_publisher(self, publisher_id):
        publisher = Publisher.query.get(publisher_id)
        if not publisher:
            return error_response("Publisher not found", error="not_found", status_code=404)

        # **Relationship Handling (One-to-Many with Nullable FK):**
        # Before deleting the publisher, set the `publisher_id` to NULL
        # for all associated books. This prevents foreign key constraint errors
        # and aligns with the nullable FK design.
        try:
            # Efficiently update associated books in bulk
            Book.query.filter(Book.publisher_id == publisher_id).update(
                {Book.publisher_id: None},
                synchronize_session=False # Use 'fetch' or False depending on needs/version
            )
            # synchronize_session='fetch' might be needed in some cases to update
            # the session state, but 'False' is often sufficient and faster here.

            publisher_name = publisher.name # Store name for logging before deletion
            db.session.delete(publisher)
            db.session.commit()
            logger.info(f"Publisher deleted: ID {publisher_id}, Name '{publisher_name}'. Associated books' publisher_id set to NULL.")
            # Return success, route will handle 204 No Content
            return success_response("Publisher deleted successfully", status_code=200)
        except Exception as e: # Catch potential DB errors during update or delete
            db.session.rollback()
            logger.error(f"Error deleting publisher {publisher_id} or updating books: {e}", exc_info=True)
            return error_response("Failed to delete publisher", error=str(e), status_code=500)