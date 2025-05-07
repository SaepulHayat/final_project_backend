def test_register_login_get_balance(client):
    # Register
    resp = client.post('/auth/register', json={
        "full_name": "Integration",
        "email": "integration@example.com",
        "password": "@GTest1234"
    })
    assert resp.status_code == 201

    # Login
    resp = client.post('/auth/login', json={
        "email": "integration@example.com",
        "password": "@GTest1234"
    })
    assert resp.status_code == 200
    token = resp.get_json()['data']['access_token']

    # Get balance
    resp = client.get('/user/balance', headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert 'balance' in resp.get_json()['data']
