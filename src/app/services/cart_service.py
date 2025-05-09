import logging
from ..model.cart import Cart
from ..model.book import Book
from ..extensions import db
from ..utils.response import create_response, error_response, success_response

logger = logging.getLogger(__name__)

class CartService:
    def add_to_cart(self, user_id, book_id, quantity=1):
        """Add a book to user's cart"""
        try:
            # Validate quantity
            if quantity <= 0:
                return error_response("Quantity must be positive", status_code=400)
                
            # Check if book exists
            book = Book.query.get(book_id)
            if not book:
                return error_response("Book not found", status_code=404)
                
            # Check if already in cart
            existing = Cart.query.filter_by(user_id=user_id, book_id=book_id).first()
            if existing:
                existing.quantity += quantity
                db.session.commit()
                return success_response(
                    "Cart updated",
                    {"cart": existing.to_dict()},
                    status_code=200
                )
                
            # Add to cart
            cart_item = Cart(user_id=user_id, book_id=book_id, quantity=quantity)
            db.session.add(cart_item)
            db.session.commit()
            
            return success_response(
                "Book added to cart",
                {"cart": cart_item.to_dict()},
                status_code=201
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Add to cart error: {str(e)}", exc_info=True)
            return error_response("Failed to add book to cart", error=str(e), status_code=500)
    
    def get_user_cart(self, user_id):
        """Get all items in user's cart"""
        try:
            cart_items = Cart.query.filter_by(user_id=user_id).all()
            
            # Calculate total
            total = sum(item.book.price * item.quantity for item in cart_items if item.book)
            
            return success_response(
                "Cart retrieved successfully",
                {
                    "cart": [item.to_dict() for item in cart_items],
                    "total": float(total)
                },
                status_code=200
            )
            
        except Exception as e:
            logger.error(f"Get cart error: {str(e)}", exc_info=True)
            return error_response("Failed to retrieve cart", error=str(e), status_code=500)
    
    def update_cart_quantity(self, cart_id, user_id, quantity):
        """Update quantity of an item in cart"""
        try:
            # Validate quantity
            if quantity <= 0:
                return error_response("Quantity must be positive", status_code=400)
                
            cart_item = Cart.query.get(cart_id)
            
            if not cart_item:
                return error_response("Cart item not found", status_code=404)
                
            if cart_item.user_id != int(user_id):
                return error_response("Unauthorized access", status_code=403)
                
            cart_item.quantity = quantity
            db.session.commit()
            
            return success_response(
                "Cart updated",
                {"cart": cart_item.to_dict()},
                status_code=200
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Update cart error: {str(e)}", exc_info=True)
            return error_response("Failed to update cart", error=str(e), status_code=500)
    
    def remove_from_cart(self, cart_id, user_id):
        """Remove an item from user's cart"""
        try:
            cart_item = Cart.query.get(cart_id)
            
            if not cart_item:
                return error_response("Cart item not found", status_code=404)
                
            if cart_item.user_id != int(user_id):
                return error_response("Unauthorized access", status_code=403)
                
            db.session.delete(cart_item)
            db.session.commit()
            
            return success_response(
                "Book removed from cart",
                {},
                status_code=200
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Remove from cart error: {str(e)}", exc_info=True)
            return error_response("Failed to remove book from cart", error=str(e), status_code=500)
    
    def clear_cart(self, user_id):
        """Clear all items in user's cart"""
        try:
            Cart.query.filter_by(user_id=user_id).delete()
            db.session.commit()
            
            return success_response(
                "Cart cleared",
                {},
                status_code=200
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Clear cart error: {str(e)}", exc_info=True)
            return error_response("Failed to clear cart", error=str(e), status_code=500)
