import pytest
from src.app.model.user import User
from src.app.util.roles import UserRoles
from src.app.extensions import db
from src.app.util.decorators import seller_required
from flask import Flask, jsonify
from flask_jwt_extended import JWTManager, create_access_token

@pytest.fixture
def seller_app(app):
    JWTManager(app)
    @app.route('/seller-only')
    @seller_required
    def seller_only():
        return jsonify({"msg": "ok"})
    return app

def test_seller_required_access(client, app):
    with app.app_context():
        # Buat user seller
        user = User(
            full_name="Seller User",
            email="seller@example.com",
            password="password123",
            role=UserRoles.SELLER.value
        )
        db.session.add(user)
        db.session.commit()
        
        # Generate token dengan role seller
        token = create_access_token(identity=user.id, additional_claims={"role": UserRoles.SELLER.value})
        response = client.get('/seller-only', headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 200, "Pastikan token mengandung role seller"

def test_seller_required_forbidden(client, app):
    with app.app_context():
        # Buat user customer
        user = User(
            full_name="Customer User",
            email="customer@example.com",
            password="password123",
            role=UserRoles.CUSTOMER.value
        )
        db.session.add(user)
        db.session.commit()
        
        # Generate token dengan role customer
        token = create_access_token(identity=user.id, additional_claims={"role": UserRoles.CUSTOMER.value})
        response = client.get('/seller-only', headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403, "Pastikan decorator mengembalikan 403 untuk role salah"
