# service/transaction_service.py
from flask import jsonify
from flask_jwt_extended import get_jwt_identity
from decimal import Decimal
from datetime import datetime
import logging

from ..model.transaction import Transaction
from ..model.user import User
from ..model.book import Book
from ..extensions import db
from ..util.validators import validate_transaction_input
from ..util.response import create_response, error_response, success_response
from ..util.roles import UserRoles

logger = logging.getLogger(__name__)

class TransactionService:
    def create_transaction(self, data, customer_id):
        try:
            # Validasi input
            validation_errors = validate_transaction_input(data)
            if validation_errors:
                return error_response(
                    "Validation failed",
                    errors=validation_errors
                )
            
            # Ambil data buku dan penjual
            book_id = data.get('book_id')
            book = Book.query.get(book_id)
            
            if not book:
                return error_response("Book not found")
            
            # Cek ketersediaan buku
            if book.quantity < int(data.get('quantity', 1)):
                return error_response("Book quantity not enough")
                
            seller_id = book.user_id
            quantity = int(data.get('quantity', 1))
            payment_method = data.get('payment_method')
            
            # Hitung total amount
            total_amount = Decimal(str(book.price)) * quantity
            
            # Cek saldo jika payment method adalah balance
            if payment_method == 'balance':
                customer = User.query.get(customer_id)
                if customer.balance < total_amount:
                    return error_response("Insufficient balance")
            
            # Buat transaksi baru
            with db.session.begin_nested():
                transaction = Transaction(
                    customer_id=customer_id,
                    seller_id=seller_id,
                    book_id=book_id,
                    amount=total_amount,
                    quantity=quantity,
                    payment_method=payment_method,
                    status='pending'
                )
                
                # Tambahkan data pengiriman jika ada
                if data.get('shipping_location_id'):
                    transaction.shipping_location_id = data.get('shipping_location_id')
                    transaction.shipping_phone = data.get('shipping_phone')
                    transaction.shipping_notes = data.get('shipping_notes')
                
                db.session.add(transaction)
                
                # Proses pembayaran jika menggunakan balance
                if payment_method == 'balance':
                    customer = User.query.get(customer_id)
                    seller = User.query.get(seller_id)
                    
                    customer.deduct_balance(total_amount)
                    seller.add_balance(total_amount)
                    transaction.status = 'paid'
                    
                    # Kurangi stok buku
                    book.quantity -= quantity
                
                db.session.commit()
            
            return success_response(
                "Transaction created successfully",
                {
                    "transaction_id": transaction.id,
                    "transaction_code": transaction.transaction_code,
                    "amount": float(transaction.amount),
                    "status": transaction.status
                }
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Transaction error: {str(e)}", exc_info=True)
            return error_response("Transaction failed", error=str(e))
    
    def get_transaction(self, transaction_id, user_id):
        try:
            transaction = Transaction.query.get(transaction_id)
            
            if not transaction:
                return error_response("Transaction not found")
            
            # Cek apakah user adalah customer atau seller
            if transaction.customer_id != user_id and transaction.seller_id != user_id:
                return error_response("Unauthorized access", code=403)
            
            return success_response(
                "Transaction details retrieved",
                transaction.to_dict()
            )
            
        except Exception as e:
            logger.error(f"Get transaction error: {str(e)}", exc_info=True)
            return error_response("Failed to retrieve transaction", error=str(e))
    
    def update_transaction_status(self, transaction_id, new_status, user_id):
        try:
            transaction = Transaction.query.get(transaction_id)
            
            if not transaction:
                return error_response("Transaction not found")
            
            # Validasi status update berdasarkan role
            user = User.query.get(user_id)
            
            # Validasi status yang dapat diubah oleh seller
            if user.role == UserRoles.SELLER and transaction.seller_id == user_id:
                if new_status not in ['processing', 'shipped', 'delivered']:
                    return error_response("Invalid status update for seller", code=403)
            
            # Validasi status yang dapat diubah oleh customer
            elif user.role == UserRoles.CUSTOMER and transaction.customer_id == user_id:
                if new_status not in ['cancelled', 'received']:
                    return error_response("Invalid status update for customer", code=403)
            else:
                return error_response("Unauthorized to update transaction status", code=403)
            
            # Update status
            transaction.status = new_status
            transaction.updated_at = datetime.utcnow()
            db.session.commit()
            
            return success_response(
                f"Transaction status updated to {new_status}",
                {"transaction_id": transaction.id, "status": transaction.status}
            )
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Update transaction error: {str(e)}", exc_info=True)
            return error_response("Failed to update transaction", error=str(e))
            
    def get_user_transactions(self, user_id, role):
        try:
            if role == UserRoles.CUSTOMER:
                transactions = Transaction.query.filter_by(customer_id=user_id).all()
                message = "Customer transactions retrieved"
            elif role == UserRoles.SELLER:
                transactions = Transaction.query.filter_by(seller_id=user_id).all()
                message = "Seller transactions retrieved"
            else:
                return error_response("Invalid role")
                
            return success_response(
                message,
                [t.to_dict() for t in transactions]
            )
            
        except Exception as e:
            logger.error(f"Get transactions error: {str(e)}", exc_info=True)
            return error_response("Failed to retrieve transactions", error=str(e))
