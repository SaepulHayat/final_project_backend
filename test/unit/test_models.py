from src.app.model.user import User
from src.app.util.roles import UserRoles

def test_user_password_hashing(app):
    user = User(full_name="Test", email="test@example.com", password="pass123")
    assert user.password_hash != "pass123"
    assert user.verify_password("pass123")
    assert not user.verify_password("wrongpass")

def test_user_role_default(app):
    user = User(full_name="Test", email="test2@example.com", password="pass123")
    assert user.role == UserRoles.CUSTOMER.value
