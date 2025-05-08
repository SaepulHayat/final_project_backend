from flask import jsonify
from ..model.user import User
import logging

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

            # Ambil info user yang mengundang (referrer)
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
