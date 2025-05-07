from flask import jsonify
from flask_jwt_extended import create_access_token, create_refresh_token
from datetime import datetime
import logging

from ..model.user import User
from ..model.blacklist_token import BlacklistToken
from ..extensions import db
from ..utils.roles import UserRoles
from ..utils.validators import validate_register_input, validate_login_input
from ..utils.security import hash_password, verify_password, generate_referral_code
from ..utils.bonus import ReferralBonusService
from ..utils.response import create_response, error_response, success_response

logger = logging.getLogger(__name__)


class AuthService:

    def register_user(self, data):
        try:
            # Validate input
            validation_errors = validate_register_input(data)
            if validation_errors:
                return error_response("Validation failed", errors=validation_errors, status_code=400)

            email = data['email'].lower()
            if User.query.filter_by(email=email).first():
                return error_response("Email already registered", status_code=409)

            referring_user = self._get_referring_user(data.get('referred_by'))
            if data.get('referred_by') and not referring_user:
                return error_response("Invalid referral code", status_code=400)

            new_user = self._create_new_user(data, referring_user)
            db.session.add(new_user)

            if referring_user and not self._process_referral_bonus(referring_user, new_user):
                db.session.rollback()
                return error_response("Referral bonus processing failed", status_code=500)

            db.session.commit()
            return success_response(
                "User registered successfully",
                {
                    "user_id": new_user.id,
                    "email": new_user.email,
                    "referral_code": new_user.referral_code
                },
                status_code=201
            )

        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            return error_response("Registration failed", error=str(e), status_code=500)

    def login_user(self, data):
        try:
            validation_errors = validate_login_input(data)
            if validation_errors:
                return error_response("Validation failed", errors=validation_errors, status_code=400)

            email = data['email'].lower()
            user = User.query.filter_by(email=email).first()

            if not user or not user.verify_password(data['password']):
                return error_response("Invalid credentials", error="unauthorized", status_code=401)

            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))

            user.last_login = datetime.utcnow()
            db.session.add(user)
            db.session.commit()

            return success_response(
                "Login successful",
                {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "user_id": user.id,
                    "email": user.email
                },
                status_code=200
            )

        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True)
            return error_response("Login failed", error=str(e), status_code=500)

    def logout_user(self, token):
        try:
            db.session.add(BlacklistToken(token=token))
            db.session.commit()
            return success_response("Logout successful", status_code=200)

        except Exception as e:
            db.session.rollback()
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return error_response("Logout failed", error=str(e), status_code=500)

    # --- Helpers ---

    def _create_new_user(self, data, referring_user=None):
        return User(
            full_name=data['full_name'],
            email=data['email'].lower(),
            password=data['password'],
            role=data.get('role', UserRoles.CUSTOMER.value),
            referral_code=generate_referral_code(),
            referred_by=referring_user.id if referring_user else None
        )

    def _get_referring_user(self, referral_code):
        if not referral_code:
            return None
        return User.query.filter_by(referral_code=referral_code).first()

    def _process_referral_bonus(self, referring_user, new_user):
        try:
            return ReferralBonusService().give_referral_bonus(referring_user, new_user)
        except Exception as e:
            logger.error(f"Referral bonus error: {str(e)}", exc_info=True)
            return False