import pytest
from app import create_app
from app.extensions import db as _db


@pytest.fixture(scope='session')
def app():
    application = create_app('testing')
    with application.app_context():
        _db.create_all()
        yield application
        _db.drop_all()


@pytest.fixture(autouse=True)
def clean_db(app):
    yield
    with app.app_context():
        for table in reversed(_db.metadata.sorted_tables):
            _db.session.execute(table.delete())
        _db.session.commit()


@pytest.fixture
def client(app):
    return app.test_client()


def _register(client, name, email, password, role='customer'):
    return client.post('/api/auth/register', json={
        'name': name, 'email': email, 'password': password, 'role': role,
    })


def _login(client, email, password):
    resp = client.post('/api/auth/login', json={'email': email, 'password': password})
    return resp.get_json()['access_token']


def _headers(token):
    return {'Authorization': f'Bearer {token}'}


@pytest.fixture
def customer_token(client):
    _register(client, 'Alice', 'alice@example.com', 'password123', 'customer')
    return _login(client, 'alice@example.com', 'password123')


@pytest.fixture
def agent_token(client):
    _register(client, 'Bob', 'bob@example.com', 'password123', 'agent')
    return _login(client, 'bob@example.com', 'password123')


@pytest.fixture
def admin_token(client):
    _register(client, 'Carol', 'carol@example.com', 'password123', 'admin')
    return _login(client, 'carol@example.com', 'password123')


@pytest.fixture
def customer_headers(customer_token):
    return _headers(customer_token)


@pytest.fixture
def agent_headers(agent_token):
    return _headers(agent_token)


@pytest.fixture
def admin_headers(admin_token):
    return _headers(admin_token)


@pytest.fixture
def sample_ticket(client, customer_headers):
    resp = client.post('/api/tickets', headers=customer_headers, json={
        'subject': 'Cannot login to my account',
        'description': 'I have been trying to login but keep getting an error message.',
        'priority': 'high',
        'category': 'technical',
        'customer_email': 'alice@example.com',
    })
    return resp.get_json()
