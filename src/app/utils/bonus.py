from decimal import Decimal  
from sqlalchemy.exc import SQLAlchemyError  
import logging  
from ..model.user import User  
from ..extensions import db  

logger = logging.getLogger(__name__)  

class ReferralBonusService:  
    """  
    Service untuk manajemen bonus referral  
    """  
    
    REFERRER_BONUS = Decimal('30000')  
    NEW_USER_BONUS = Decimal('20000')  
    
    @classmethod  
    def give_referral_bonus(cls, referring_user: User, new_user: User) -> bool:  
        """  
        Proses bonus referral dengan referring_user yang sudah divalidasi  
        
        Args:  
            referring_user (User): User yang merujuk (sudah valid)  
            new_user (User): User baru  
        
        Returns:  
            bool: True jika bonus berhasil diproses  
        """  
        try:  
            if not cls._validate_referral_conditions(referring_user, new_user):  
                logger.warning("Referral validation failed")  
                return False  
            
            cls._apply_referral_bonus(  
                referring_user=referring_user,  
                new_user=new_user,  
                referrer_bonus=cls.REFERRER_BONUS,  
                new_user_bonus=cls.NEW_USER_BONUS  
            )  
            return True  
        
        except SQLAlchemyError as e:  
            logger.error(f"Database error in referral bonus: {e}")  
            db.session.rollback()  
            return False  
        
        except Exception as e:  
            logger.error(f"Unexpected error in referral bonus: {e}")  
            return False
    
    @classmethod  
    def _find_referring_user(cls, referral_code: str) -> User:  
        """  
        Cari user yang merujuk berdasarkan kode referral  
        
        Args:  
            referral_code (str): Kode referral  
        
        Returns:  
            User: User yang merujuk, atau None  
        """  
        return User.query.filter_by(  
            referral_code=referral_code,   
            is_active=True  
        ).first()  
    
    @classmethod  
    def _validate_referral_conditions(cls, referring_user: User, new_user: User) -> bool:  
        """  
        Validasi kondisi referral  
        
        Args:  
            referring_user (User): User yang merujuk  
            new_user (User): User baru  
        
        Returns:  
            bool: True jika kondisi referral valid  
        """  
        if referring_user.id == new_user.id:  
            logger.warning("Self-referral attempt detected")  
            return False  
        
        existing_referral = User.query.filter_by(referred_by=referring_user.id).count()  
        
        MAX_REFERRALS = 10  
        if existing_referral >= MAX_REFERRALS:  
            logger.warning(f"Max referrals reached for user {referring_user.id}")  
            return False  
        
        return True  
    
    @classmethod  
    def _apply_referral_bonus(  
        cls,   
        referring_user: User,   
        new_user: User,   
        referrer_bonus: Decimal,   
        new_user_bonus: Decimal  
    ):  
    
        try:  
            referring_user.balance += referrer_bonus  
            new_user.balance += new_user_bonus  
            referring_user.total_referred = (referring_user.total_referred or 0) + 1  
            new_user.referred_by = referring_user.id  
            
            
            db.session.add(referring_user)  
            db.session.add(new_user)  
            
            logger.info(f"Referral bonus applied: Referrer {referring_user.id}, New User {new_user.id}")  
        
        except SQLAlchemyError as e:  
            logger.error(f"Error applying referral bonus: {e}")  
            raise

