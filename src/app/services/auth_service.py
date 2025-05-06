from flask import jsonify  
from flask_jwt_extended import create_access_token, create_refresh_token  
from decimal import Decimal
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
            # Validasi input
            validation_errors = validate_register_input(data)
            if validation_errors:
                return error_response(
                    "Validation failed",
                    errors=validation_errors,
                    status_code=400 # Explicitly set 400
                )

            # Cek email sudah terdaftar
            email = data['email'].lower()
            if User.query.filter_by(email=email).first():
                return error_response("Email already registered", status_code=409) # Use 409 Conflict

            # Proses referral
            referring_user = None
            referral_code = data.get('referred_by')

            if referral_code:
                referring_user = User.query.filter_by(referral_code=referral_code).first()
                if not referring_user:
                    # Referral code provided but not found
                    return error_response("Invalid referral code", status_code=400) # Bad request

            # Buat user baru
            new_user = self._create_new_user(data, referring_user)
            db.session.add(new_user)
            
            # Proses bonus referral
            if referring_user:
                try:
                    # Panggil ReferralBonusService
                    success = ReferralBonusService().give_referral_bonus(
                        referring_user=referring_user,
                        new_user=new_user
                    )
                    
                    if not success:
                        logger.error("Failed to process referral bonus")
                        db.session.rollback()
                        # Internal server error during bonus processing
                        return error_response("Referral bonus processing failed", status_code=500)

                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Referral bonus error: {str(e)}", exc_info=True)
                    # Internal server error during bonus processing
                    return error_response("Referral processing failed", error=str(e), status_code=500)

            db.session.commit()

            return success_response(
                "User registered successfully",
                {
                    "user_id": new_user.id,
                    "email": new_user.email,
                    "referral_code": new_user.referral_code
                },
                status_code=201 # Use 201 Created
            )

        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            # General internal server error during registration
            return error_response("Registration failed", error=str(e), status_code=500)


    def _create_new_user(self, data, referring_user=None):
        """  
        Membuat instance user baru  
        """  
        return User(  
            full_name=data['full_name'],  
            email=data['email'].lower(),  
            password=data['password'],  
            role=data.get('role', UserRoles.CUSTOMER.value),  
            referral_code=generate_referral_code(),  
            referred_by=referring_user.id if referring_user else None  
        )  

    def login_user(self, data):
        try:
            # Validasi input login
            validation_errors = validate_login_input(data)
            if validation_errors:
                return error_response(
                    "Validation failed",
                    errors=validation_errors,
                    status_code=400 # Explicitly set 400
                )

            # Cari user berdasarkan email
            email = data['email'].lower()
            user = User.query.filter_by(email=email).first()

            if not user:
                # User not found, treat as unauthorized
                return error_response("Invalid credentials", error="user_not_found", status_code=401)

            # Verifikasi password
            if not user.verify_password(data['password']):
                # Incorrect password, treat as unauthorized
                return error_response("Invalid credentials", error="invalid_password", status_code=401)

            # Buat access dan refresh token
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))

            # Update last log.id)

            # Update last login
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
                status_code=200 # OK
            )

        except Exception as e:
            logger.error(f"Login error: {str(e)}", exc_info=True) # Add logging
            return error_response(
                "Login failed",
                error=str(e),
                status_code=500 # Internal Server Error
            )


    def logout_user(self, token):
        """  
        Proses logout dengan blacklist token  
        """  
        try:  
            # Tambahkan token ke blacklist  
            blacklist_token = BlacklistToken(token=token)  
            db.session.add(blacklist_token)  
            db.session.commit()  

            return success_response("Logout successful", status_code=200) # OK

        except Exception as e:
            db.session.rollback()
            logger.error(f"Logout error: {str(e)}", exc_info=True)
            return error_response("Logout failed", error=str(e), status_code=500) # Internal Server Error

