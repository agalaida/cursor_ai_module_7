"""Run in its own process (see test_rate_limit.py) so the global db/jwt/limiter
singletons never get shared with the rest of the test session — flipping
RATELIMIT_ENABLED on an app that already served a request raises inside Flask."""
import json
import config
from app import create_app

config.TestingConfig.RATELIMIT_ENABLED = True
app = create_app('testing')

with app.app_context():
    from app.extensions import db
    db.create_all()

client = app.test_client()
client.post('/api/auth/register', json={
    'name': 'Rate Test', 'email': 'ratetest@example.com', 'password': 'password123',
})

statuses = []
for _ in range(11):
    resp = client.post('/api/auth/login', json={
        'email': 'ratetest@example.com', 'password': 'wrongpassword',
    })
    statuses.append(resp.status_code)

print(json.dumps(statuses))
