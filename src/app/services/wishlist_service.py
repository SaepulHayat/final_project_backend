import logging
from ..model.wishlist import Wishlist
from ..model.book import Book
from ..extensions import db
from ..utils.response import create_response, error_response, success_response

logger = logging.getLogger(__name__)

class WishlistService:
    def add_to_wishlist(self, user_id, book_id):
        """Add a book to user's wishlist"""
        try:
            # Check if book exists
            book = Book.query.get(book_id)
            if not book:
                return error_response("Book not found", status_code=404)
                
            # Check if already in wishlist
            existing = Wishlist.query.filter_by(user_id=user_id, book_id=book_id).first()
            if existing:
                return success_response(
                    "Book already in wishlist",
                    {"wishlist": existing.to_dict()},
                    status_code=200
                )
                
            # Add to wishlist
            wishlist_item = Wishlist(user_id=user_id, book_id=book_id)
            db.session.add(wishlist_item)
            db.session.commit()
            
            return success_response(
                "Book added to wishlist",
                {"wishlist": wishlist_item.to_dict()},
                status_code=201
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Add to wishlist error: {str(e)}", exc_info=True)
            return error_response("Failed to add book to wishlist", error=str(e), status_code=500)
    
    def get_user_wishlist(self, user_id):
        """Get all items in user's wishlist"""
        try:
            wishlist_items = Wishlist.query.filter_by(user_id=user_id).all()
            
            return success_response(
                "Wishlist retrieved successfully",
                {"wishlist": [item.to_dict() for item in wishlist_items]},
                status_code=200
            )
            
        except Exception as e:
            logger.error(f"Get wishlist error: {str(e)}", exc_info=True)
            return error_response("Failed to retrieve wishlist", error=str(e), status_code=500)
    
    def remove_from_wishlist(self, wishlist_id, user_id):
        """Remove an item from user's wishlist"""
        try:
            wishlist_item = Wishlist.query.get(wishlist_id)
            
            if not wishlist_item:
                return error_response("Wishlist item not found", status_code=404)
                
            if wishlist_item.user_id != int(user_id):
                return error_response("Unauthorized access", status_code=403)
                
            db.session.delete(wishlist_item)
            db.session.commit()
            
            return success_response(
                "Book removed from wishlist",
                {},
                status_code=200
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Remove from wishlist error: {str(e)}", exc_info=True)
            return error_response("Failed to remove book from wishlist", error=str(e), status_code=500)
