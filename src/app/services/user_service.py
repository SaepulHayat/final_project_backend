from flask import jsonify
import logging

from ..model.user import User
""" from ..model.location import Location, City """
from ..extensions import db

logger = logging.getLogger(__name__)

class UserService:
    def get_referral_info(self, user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    "status": "error",
                    "message": "User not found"
                }), 404

            referrer = None
            if user.referred_by:
                referrer_user = User.query.get(user.referred_by)
                if referrer_user:
                    referrer = {
                        "id": referrer_user.id,
                        "full_name": referrer_user.full_name,
                        "email": referrer_user.email,
                        "referral_code": referrer_user.referral_code
                    }

            referred_users = User.query.filter_by(referred_by=user.id).all()

            return jsonify({
                "status": "success",
                "data": {
                    "user_id": user.id,
                    "full_name": user.full_name,
                    "referral_code": user.referral_code,
                    "referred_by": user.referred_by,
                    "referrer_info": referrer,  # <--- tampilkan info referrer di sini
                    "referred_users": [u.full_name for u in referred_users],
                    "total_referrals": len(referred_users)
                }
            }), 200

        except Exception as e:
            logger.error(f"Error getting referral info: {str(e)}", exc_info=True)
            return jsonify({
                "status": "error",
                "message": "Failed to get referral information"
            }), 500


    def get_balance(self, user_id):
        """Get user's current balance."""
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    "status": "error",
                    "message": "User not found"
                }), 404

            return jsonify({
                "status": "success",
                "data": {
                    "user_id": user.id,
                    "full_name": user.full_name,
                    "balance": float(user.balance)
                }
            }), 200

        except Exception as e:
            logger.error(f"Error getting balance: {str(e)}", exc_info=True)
            return jsonify({
                "status": "error",
                "message": "Failed to get balance"
            }), 500
        
    def get_all_users(self):
        try:
            users = User.query.all()
            return jsonify({
                "status": "success",
                "data": [user.to_dict() for user in users]
            }), 200
        except Exception as e:
            logger.error(f"Error getting all users: {str(e)}", exc_info=True)
            return jsonify({
                "status": "error",
                "message": "Failed to get users"
            }), 500

    def get_user_by_id(self, user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({"status": "error", "message": "User not found"}), 404

            return jsonify({"status": "success", "data": user.to_dict()}), 200
        except Exception as e:
            logger.error(f"Error getting user by ID: {str(e)}", exc_info=True)
            return jsonify({
                "status": "error",
                "message": "Failed to get user"
            }), 500

    def update_user(self, user_id, data):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({"status": "error", "message": "User not found"}), 404

            # Update allowed fields
            user.full_name = data.get('full_name', user.full_name)
            user.email = data.get('email', user.email)

            db.session.commit()
            return jsonify({"status": "success", "message": "User updated successfully", "data": user.to_dict()}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating user: {str(e)}", exc_info=True)
            return jsonify({"status": "error", "message": "Failed to update user"}), 500

    def delete_user_by_id(self, user_id):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({"status": "error", "message": "User not found"}), 404

            db.session.delete(user)
            db.session.commit()
            return jsonify({"status": "success", "message": "User deleted successfully"}), 200
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error deleting user: {str(e)}", exc_info=True)
            return jsonify({"status": "error", "message": "Failed to delete user"}), 500
        
    """ def update_location(self, user_id, data):
        try:
            user = User.query.get(user_id)
            if not user:
                return jsonify({"status": "error", "message": "User not found"}), 404

            city_id = data.get("city_id")
            address = data.get("address")

            if not city_id or not address:
                return jsonify({
                    "status": "error",
                    "message": "Both city_id and address are required"
                }), 400

            city = City.query.get(city_id)
            if not city:
                return jsonify({"status": "error", "message": "City not found"}), 404

            # If user already has a location, update it
            if user.location:
                user.location.city = city
                user.location.address = address
            else:
                new_location = Location(
                    user_id=user.id,
                    city=city,
                    address=address
                )
                db.session.add(new_location)
                user.location = new_location

            db.session.commit()
            return jsonify({
                "status": "success",
                "message": "Location updated successfully",
                "data": user.to_dict(include_location=True)
            }), 200

        except Exception as e:
            db.session.rollback()
            logger.error(f"Error updating location: {str(e)}", exc_info=True)
            return jsonify({
                "status": "error",
                "message": "Failed to update location"
            }), 500 """
