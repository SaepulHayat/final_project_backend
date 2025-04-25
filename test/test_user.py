import pytest
from src.app import create_app
from src.app.extensions import db
from src.app.model.user import User

@pytest.fixture
def app():
    app = create_app()
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'  # Gunakan database in-memory untuk pengujian
    app.config['TESTING'] = True
    with app.app_context():
        db.create_all()  # Buat tabel
        yield app
        db.session.remove()
        db.drop_all() # Hapus tabel setelah pengujian

@pytest.fixture
def client(app):
    return app.test_client()

def test_create_user(app):
    """Test untuk menambahkan user ke database."""
    with app.app_context():
        user = User(
            username="testuser",
            email="testuser@example.com",
            password_hash="hashedpassword",
            balance=100.00,
            referral_code="ABC123",
            role="user"
        )
        db.session.add(user)
        db.session.commit()
        
        # # Debugging: Print jumlah user di database
        # print(f"User count: {User.query.count()}")
        # print(f"First user: {User.query.first()}")

        # Verifikasi user berhasil ditambahkan
        assert User.query.count() == 1
        assert User.query.first().username == "testuser"
        
def test_duplicate_email(app):
    """Test untuk memastikan email unik."""
    with app.app_context():
        user1 = User(
            username="user1",
            email="duplicate@example.com",
            password_hash="hashedpassword",
            balance=50.00,
            referral_code="CODE123",
            role="user"
        )
        user2 = User(
            username="user2",
            email="duplicate@example.com",  # Email yang sama
            password_hash="hashedpassword",
            balance=75.00,
            referral_code="CODE456",
            role="user"
        )
        db.session.add(user1)
        db.session.commit()

        # Menambahkan user kedua dengan email yang sama harus gagal
        with pytest.raises(Exception):
            db.session.add(user2)
            db.session.commit()