import logging
from sqlalchemy import or_ # Import 'or_' for search query
from ..extensions import db
from ..model.author import Author
from ..utils.response import success_response, error_response

logger = logging.getLogger(__name__)

class AuthorService:
    def create_author(self, data):
        """
        Creates a new author.
        Args:
            data (dict): Dictionary containing author data (first_name, last_name, bio).
        Returns:
            dict: A response dictionary indicating success or failure.
        """
        try:
            first_name = data.get('first_name')
            last_name = data.get('last_name')
            bio = data.get('bio')

            # Basic validation
            if not first_name:
                return error_response("First name is required")

            # Check if author already exists (optional, based on name combination?)
            # existing_author = Author.query.filter_by(first_name=first_name, last_name=last_name).first()
            # if existing_author:
            #     return error_response("Author with this name already exists")

            new_author = Author(
                first_name=first_name,
                last_name=last_name,
                bio=bio
            )
            db.session.add(new_author)
            db.session.commit()

            logger.info(f"Author created successfully: ID {new_author.id}")
            return success_response(
                "Author created successfully",
                data={
                    "id": new_author.id,
                    "first_name": new_author.first_name,
                    "last_name": new_author.last_name,
                    "bio": new_author.bio,
                    "created_at": new_author.created_at.isoformat(),
                    "updated_at": new_author.updated_at.isoformat()
                }
            )

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error creating author: {str(e)}", exc_info=True)
            return error_response("Failed to create author", error=str(e))

    # --- Placeholder for other CRUD methods ---

    def get_all_authors(self, page=1, per_page=10, search=None):
        """
        Gets a paginated list of authors, optionally filtered by a search term.
        Args:
            page (int): The page number to retrieve.
            per_page (int): The number of items per page.
            search (str, optional): A search term to filter authors by first or last name.
        Returns:
            dict: A response dictionary containing the list of authors and pagination info.
        """
        try:
            query = Author.query

            # Apply search filter if provided
            if search:
                search_term = f"%{search}%"
                query = query.filter(
                    or_(
                        Author.first_name.ilike(search_term),
                        Author.last_name.ilike(search_term)
                        # Add Author.bio.ilike(search_term) if searching bio is desired
                    )
                )

            # Apply ordering (optional, e.g., by name or creation date)
            query = query.order_by(Author.first_name, Author.last_name)

            # Paginate the results
            pagination = query.paginate(page=page, per_page=per_page, error_out=False)
            authors = pagination.items
            total_pages = pagination.pages
            total_authors = pagination.total

            # Format the output data
            authors_data = [
                {
                    "id": author.id,
                    "first_name": author.first_name,
                    "last_name": author.last_name,
                    "bio": author.bio,
                    "created_at": author.created_at.isoformat(),
                    "updated_at": author.updated_at.isoformat()
                } for author in authors
            ]

            pagination_data = {
                "current_page": page,
                "per_page": per_page,
                "total_pages": total_pages,
                "total_items": total_authors
            }

            logger.info(f"Retrieved {len(authors_data)} authors (page {page}/{total_pages})")
            return success_response(
                "Authors retrieved successfully",
                data={"authors": authors_data, "pagination": pagination_data}
            )

        except Exception as e:
            logger.error(f"Error retrieving authors: {str(e)}", exc_info=True)
            return error_response("Failed to retrieve authors", error=str(e))

    def get_author_by_id(self, author_id):
        """
        Gets a single author by their ID.
        Args:
            author_id (int): The ID of the author to retrieve.
        Returns:
            dict: A response dictionary containing author data or an error message.
        """
        try:
            author = Author.query.get(author_id)

            if not author:
                logger.warning(f"Author not found with ID: {author_id}")
                return error_response("Author not found") # Route will handle 404

            logger.info(f"Author retrieved successfully: ID {author.id}")
            return success_response(
                "Author retrieved successfully",
                data={
                    "id": author.id,
                    "first_name": author.first_name,
                    "last_name": author.last_name,
                    "bio": author.bio,
                    "created_at": author.created_at.isoformat(),
                    "updated_at": author.updated_at.isoformat()
                    # Consider adding book list or count if needed later
                }
            )

        except Exception as e:
            logger.error(f"Error retrieving author {author_id}: {str(e)}", exc_info=True)
            return error_response("Failed to retrieve author", error=str(e))

    def update_author(self, author_id, data):
        """
        Updates an existing author's details.
        Args:
            author_id (int): The ID of the author to update.
            data (dict): Dictionary containing the fields to update (first_name, last_name, bio).
                         Only provided fields will be updated.
        Returns:
            dict: A response dictionary indicating success or failure.
        """
        try:
            author = Author.query.get(author_id)

            if not author:
                logger.warning(f"Attempted to update non-existent author with ID: {author_id}")
                return error_response("Author not found") # Route will handle 404

            updated = False
            # Update fields only if they are present in the data payload
            if 'first_name' in data and data['first_name']: # Ensure not empty if required
                author.first_name = data['first_name']
                updated = True
            if 'last_name' in data: # Allow setting last_name to None/empty if intended
                author.last_name = data['last_name']
                updated = True
            if 'bio' in data:
                author.bio = data['bio']
                updated = True

            if not updated:
                return error_response("No update data provided") # Or maybe success with no changes?

            # Note: updated_at is handled automatically by server_onupdate=func.now() in the model
            db.session.add(author) # Add to session, although it's already tracked
            db.session.commit()

            logger.info(f"Author updated successfully: ID {author.id}")
            return success_response(
                "Author updated successfully",
                data={
                    "id": author.id,
                    "first_name": author.first_name,
                    "last_name": author.last_name,
                    "bio": author.bio,
                    "created_at": author.created_at.isoformat(),
                    "updated_at": author.updated_at.isoformat()
                }
            )

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating author {author_id}: {str(e)}", exc_info=True)
            return error_response("Failed to update author", error=str(e))

    def delete_author(self, author_id):
        """
        Deletes an author and their associated books (due to cascade).
        Args:
            author_id (int): The ID of the author to delete.
        Returns:
            dict: A response dictionary indicating success or failure.
        """
        try:
            author = Author.query.get(author_id)

            if not author:
                logger.warning(f"Attempted to delete non-existent author with ID: {author_id}")
                return error_response("Author not found") # Route will handle 404

            # The 'cascade="all, delete-orphan"' on Author.books relationship
            # means associated books will be deleted automatically when the author is deleted.
            db.session.delete(author)
            db.session.commit()

            logger.info(f"Author deleted successfully: ID {author_id}")
            # Return success with no data, as the author is gone
            return success_response("Author deleted successfully")

        except Exception as e:
            db.session.rollback()
            # Check for specific integrity errors if needed, e.g., if cascade wasn't set up
            logger.error(f"Error deleting author {author_id}: {str(e)}", exc_info=True)
            return error_response("Failed to delete author", error=str(e))