def test_register_success(client):
    resp = client.post('/api/auth/register', json={
        'name': 'John Doe',
        'email': 'john@example.com',
        'password': 'password123',
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert 'user' in data
    assert data['user']['email'] == 'john@example.com'
    assert data['user']['role'] == 'customer'


def test_register_duplicate_email(client):
    payload = {'name': 'Jane', 'email': 'jane@example.com', 'password': 'password123'}
    client.post('/api/auth/register', json=payload)
    resp = client.post('/api/auth/register', json=payload)
    assert resp.status_code == 409
    assert resp.get_json()['code'] == 'CONFLICT'


def test_register_invalid_email(client):
    resp = client.post('/api/auth/register', json={
        'name': 'Bad', 'email': 'not-an-email', 'password': 'password123',
    })
    assert resp.status_code == 400
    assert 'email' in resp.get_json()['errors']


def test_login_success(client):
    client.post('/api/auth/register', json={
        'name': 'User', 'email': 'user@example.com', 'password': 'password123',
    })
    resp = client.post('/api/auth/login', json={
        'email': 'user@example.com', 'password': 'password123',
    })
    assert resp.status_code == 200
    assert 'access_token' in resp.get_json()


def test_login_wrong_password(client):
    client.post('/api/auth/register', json={
        'name': 'User2', 'email': 'user2@example.com', 'password': 'password123',
    })
    resp = client.post('/api/auth/login', json={
        'email': 'user2@example.com', 'password': 'wrongpassword',
    })
    assert resp.status_code == 401


def test_me_returns_current_user(client, customer_headers):
    resp = client.get('/api/auth/me', headers=customer_headers)
    assert resp.status_code == 200
    assert resp.get_json()['email'] == 'alice@example.com'


def test_me_without_token(client):
    resp = client.get('/api/auth/me')
    assert resp.status_code == 401
