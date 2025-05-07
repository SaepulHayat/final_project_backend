from src.app.service.user_service import UserService
from src.app.model.user import User
from src.app.util.roles import UserRoles
from src.app.extensions import db

def test_get_referral_info(client, app):
    service = UserService()
    with app.app_context():
        referrer = User(full_name="Referrer", email="referrer@example.com", password="refpass")
        db.session.add(referrer)
        db.session.commit()
        referred = User(full_name="Referred", email="referred@example.com", password="refpass", referred_by=referrer.id)
        db.session.add(referred)
        db.session.commit()
        response, status = service.get_referral_info(referrer.id)
        assert status == 200
        assert response.json['data']['user_id'] == referrer.id

def test_get_balance(client, app):
    service = UserService()
    with app.app_context():
        user = User(full_name="Balance", email="balance@example.com", password="pass", balance=10000)
        db.session.add(user)
        db.session.commit()
        response, status = service.get_balance(user.id)
        assert status == 200
        assert response.json['data']['balance'] == 10000.0
