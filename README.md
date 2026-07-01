# Customer Support Ticket API

A RESTful API for managing customer support tickets, built with Flask, SQLAlchemy, Marshmallow, JWT authentication, and Swagger UI.

## Stack

- **Flask** 3.1 — web framework
- **Flask-SQLAlchemy** — ORM (SQLite for dev/test, PostgreSQL-ready)
- **Flask-JWT-Extended** — JWT authentication
- **Marshmallow** — schema validation and serialization
- **flasgger** — Swagger UI documentation
- **Flask-Limiter** — rate limiting
- **bcrypt** — password hashing (cost factor 12)
- **pytest + pytest-cov** — testing (88% coverage)

## Setup

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Running

```bash
flask run
# or
python run.py
```

Swagger UI: http://localhost:5000/apidocs

## Environment variables

| Variable          | Default                          | Description             |
|-------------------|----------------------------------|-------------------------|
| `SECRET_KEY`      | (insecure default)               | Flask secret key        |
| `JWT_SECRET_KEY`  | (insecure default)               | JWT signing key         |
| `DATABASE_URL`    | `sqlite:///dev.db`               | SQLAlchemy database URI |
| `FLASK_ENV`       | `development`                    | Config profile          |
| `MAIL_SERVER`     | `localhost`                      | SMTP host               |
| `MAIL_PORT`       | `25`                             | SMTP port               |

**Always set `SECRET_KEY` and `JWT_SECRET_KEY` in production.**

## Running tests

```bash
pytest                              # all tests
pytest --cov=app --cov-report=html  # with HTML coverage report
pytest tests/test_auth.py -v        # single file
```

## API Endpoints

### Authentication

| Method | Path               | Auth | Description       |
|--------|--------------------|------|-------------------|
| POST   | /api/auth/register | No   | Register user     |
| POST   | /api/auth/login    | No   | Login, get token  |
| POST   | /api/auth/logout   | Yes  | Logout            |
| GET    | /api/auth/me       | Yes  | Current user info |

### Tickets

| Method | Path                             | Roles          | Description        |
|--------|----------------------------------|----------------|--------------------|
| GET    | /api/tickets                     | all            | List tickets       |
| POST   | /api/tickets                     | all            | Create ticket      |
| GET    | /api/tickets/:id                 | owner/agent/admin | Get ticket      |
| PUT    | /api/tickets/:id                 | agent/admin    | Update ticket      |
| DELETE | /api/tickets/:id                 | admin          | Delete ticket      |
| PUT    | /api/tickets/:id/status          | agent/admin    | Change status      |
| PUT    | /api/tickets/:id/priority        | agent/admin    | Change priority    |
| POST   | /api/tickets/:id/assign          | admin          | Assign to agent    |
| GET    | /api/tickets/:id/history         | agent/admin    | Assignment history |
| POST   | /api/tickets/:id/comments        | owner/agent/admin | Add comment     |
| GET    | /api/tickets/:id/comments        | owner/agent/admin | Get comments    |

### Users & Agents

| Method | Path                            | Roles | Description             |
|--------|---------------------------------|-------|-------------------------|
| GET    | /api/users                      | admin | List all users          |
| GET    | /api/users/:id                  | admin | Get user                |
| PUT    | /api/users/:id                  | admin | Update user             |
| GET    | /api/agents                     | admin | List agents             |
| GET    | /api/agents/:id/tickets         | admin | Agent's tickets         |
| PUT    | /api/agents/:id/availability    | agent | Update availability     |

### Admin & Reports

| Method | Path                         | Description         |
|--------|------------------------------|---------------------|
| GET    | /api/admin/dashboard         | Dashboard metrics   |
| GET    | /api/admin/reports/tickets   | Ticket report       |
| GET    | /api/admin/reports/agents    | Agent performance   |
| GET    | /api/admin/reports/sla       | SLA compliance      |
| POST   | /api/admin/reports/export    | Export to CSV       |

## Ticket status transitions (FR-012)

```
open → assigned, closed
assigned → in_progress, closed
in_progress → waiting, resolved, closed
waiting → in_progress
resolved → closed, reopened
closed → reopened (within 7 days only)
reopened → in_progress
```

## Priority SLA

| Priority | First response | Resolution |
|----------|---------------|------------|
| urgent   | 2 hours       | 24 hours   |
| high     | 4 hours       | 48 hours   |
| medium   | 8 hours       | 5 days     |
| low      | 24 hours      | 10 days    |

## Example workflow

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Alice","email":"alice@example.com","password":"password123"}'

# 2. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"alice@example.com","password":"password123"}'
# → {"access_token": "<token>"}

# 3. Create ticket
curl -X POST http://localhost:5000/api/tickets \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"subject":"Cannot login","description":"I keep getting an error when I try to log in to my account.","priority":"high","category":"technical","customer_email":"alice@example.com"}'

# 4. List tickets
curl http://localhost:5000/api/tickets \
  -H "Authorization: Bearer <token>"
```
