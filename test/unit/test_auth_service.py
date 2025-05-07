from src.app.model.user import User
from src.app.service.auth_service import AuthService
from src.app.extensions import db

def test_register_user_success(client, app):
    service = AuthService()
    data = {
        "full_name": "John Doe",
        "email": "john@example.com",
        "password": "password123"
    }
    with app.app_context():
        result = service.register_user(data)
        assert result['status'] == 'success'
        user = User.query.filter_by(email="john@example.com").first()
        assert user is not None

def test_register_user_duplicate_email(client, app):
    service = AuthService()
    data = {
        "full_name": "Jane Doe",
        "email": "jane@example.com", 
        "password": "@SecurePass123!"  
    }

    with app.app_context():
        # Bersihkan database sebelum test
        db.session.query(User).delete()
        db.session.commit()

        # Registrasi pertama (harus sukses)
        result = service.register_user(data)
        assert result['status'] == 'success', "Registrasi pertama gagal, cek validasi input"

        # Registrasi kedua dengan email sama (harus error)
        result = service.register_user(data)
        assert result['status'] == 'error', "Registrasi duplikat seharusnya gagal"
        assert "already registered" in result['message'], "Pesan error spesifik"


def test_login_user_success(client, app):
    with app.app_context():
        # Registrasi user dengan password valid
        data = {
            "full_name": "Login User",
            "email": "login@example.com",
            "password": "SecurePass123!"
        }
        AuthService().register_user(data)
        
        # Login
        login_data = {
            "email": "login@example.com",
            "password": "SecurePass123!"
        }
        result = AuthService().login_user(login_data)
        assert result['status'] == 'success', "Pastikan password di-hash dengan benar"
        assert 'access_token' in result['data']

def test_login_user_wrong_password(client, app):
    with app.app_context():
        # Registrasi user
        data = {
            "full_name": "Wrong Pass",
            "email": "wrongpass@example.com",
            "password": "SecurePass123!"
        }
        AuthService().register_user(data)
        
        # Login dengan password salah
        login_data = {
            "email": "wrongpass@example.com",
            "password": "WrongPassword!"
        }
        result = AuthService().login_user(login_data)
        assert result['status'] == 'error'
        assert 'Invalid credentials' in result['message'], "Pisahkan error validasi dan kredensial"
