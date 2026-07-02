from datetime import timedelta
import bcrypt
from flask_jwt_extended import create_access_token
from app.models.user import User


def test_sql_injection_in_login_email(client):
    """TC-301: malicious input must not break the query or leak table contents."""
    resp = client.post('/api/auth/login', json={
        'email': "'; DROP TABLE users; --",
        'password': 'anything',
    })
    assert resp.status_code in (400, 401)
    with client.application.app_context():
        assert User.query.count() >= 0  # table still exists and is queryable


def test_xss_sanitized_in_ticket_description(client, customer_headers):
    """TC-302: script tags in free-text fields must be escaped, never stored raw."""
    payload = "<script>alert('xss')</script>"
    resp = client.post('/api/tickets', headers=customer_headers, json={
        'subject': 'Valid subject line here',
        'description': f'Attack attempt: {payload} rest of a long enough description.',
        'customer_email': 'alice@example.com',
    })
    assert resp.status_code == 201
    description = resp.get_json()['description']
    assert '<script>' not in description
    assert '&lt;script&gt;' in description


def test_xss_sanitized_in_comment_content(client, customer_headers, sample_ticket):
    payload = "<img src=x onerror=alert('XSS')>"
    resp = client.post(f'/api/tickets/{sample_ticket["id"]}/comments',
                       headers=customer_headers,
                       json={'content': payload, 'is_internal': False})
    assert resp.status_code == 201
    assert '<img' not in resp.get_json()['content']


def test_xss_sanitized_in_admin_user_update(client, admin_headers, customer_headers):
    """Regression test: admin PUT /users/<id> must sanitize `name` like every other write path."""
    users = client.get('/api/users', headers=admin_headers).get_json()
    customer = next(u for u in users if u['role'] == 'customer')
    resp = client.put(f'/api/users/{customer["id"]}',
                      headers=admin_headers,
                      json={'name': "<script>alert('xss')</script>"})
    assert resp.status_code == 200
    assert '<script>' not in resp.get_json()['name']


def test_password_hashing_verification(client):
    resp = client.post('/api/auth/register', json={
        'name': 'Hash Test', 'email': 'hashtest@example.com', 'password': 'TestPass123!',
    })
    user_id = resp.get_json()['user']['id']

    with client.application.app_context():
        user = User.query.get(user_id)
        assert user.password_hash != 'TestPass123!'
        assert user.password_hash.startswith('$2b$')
        assert bcrypt.checkpw('TestPass123!'.encode(), user.password_hash.encode())


def test_invalid_jwt_token_rejected(client):
    resp = client.get('/api/auth/me', headers={'Authorization': 'Bearer not-a-real-token'})
    assert resp.status_code in (401, 422)


def test_expired_jwt_token_rejected(client, app):
    with app.app_context():
        expired_token = create_access_token(identity='1', expires_delta=timedelta(seconds=-1))
    resp = client.get('/api/auth/me', headers={'Authorization': f'Bearer {expired_token}'})
    assert resp.status_code == 401


def test_customer_cannot_access_other_customers_ticket(client, sample_ticket):
    """IDOR check: a second customer must not read the first customer's ticket by guessing its id."""
    client.post('/api/auth/register', json={
        'name': 'Mallory', 'email': 'mallory@example.com', 'password': 'password123',
    })
    login = client.post('/api/auth/login', json={
        'email': 'mallory@example.com', 'password': 'password123',
    })
    mallory_headers = {'Authorization': f'Bearer {login.get_json()["access_token"]}'}

    resp = client.get(f'/api/tickets/{sample_ticket["id"]}', headers=mallory_headers)
    assert resp.status_code == 403
