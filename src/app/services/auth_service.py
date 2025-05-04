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
                    errors=validation_errors
                )

            # Cek email sudah terdaftar
            email = data['email'].lower()
            if User.query.filter_by(email=email).first():
                return error_response("Email already registered")

            # Proses referral
            referring_user = None
            referral_code = data.get('referred_by')

            if referral_code:
                referring_user = User.query.filter_by(referral_code=referral_code).first()
                if not referring_user:
                    return error_response("Invalid referral code")

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
                        return error_response("Referral bonus processing failed")
                        
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Referral bonus error: {str(e)}", exc_info=True)
                    return error_response("Referral processing failed", error=str(e))
            
            db.session.commit()

            return success_response(
                "User registered successfully",
                {
                    "user_id": new_user.id,
                    "email": new_user.email,
                    "referral_code": new_user.referral_code
                }
            )

        except Exception as e:
            db.session.rollback()
            logger.error(f"Registration error: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': "Registration failed",
                'error': str(e)
            }


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
                    errors=validation_errors
                )

            # Cari user berdasarkan email
            email = data['email'].lower()
            user = User.query.filter_by(email=email).first()
            
            if not user:
                return error_response("User not found")

            # Verifikasi password
            if not user.verify_password(data['password']):
                return error_response("Invalid credentials")

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
                }
            )

        except Exception as e:
            return error_response(
                "Login failed",
                error=str(e)
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

            return success_response("Logout successful")  
        
        except Exception as e:  
            db.session.rollback()  
            logger.error(f"Logout error: {str(e)}", exc_info=True)  
            return error_response("Logout failed", error=str(e))  


