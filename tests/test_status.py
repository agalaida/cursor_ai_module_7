from datetime import datetime, timezone, timedelta
from app.extensions import db
from app.models.ticket import Ticket


def test_valid_status_transition(client, agent_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    # assign first so we can move to in_progress
    resp = client.put(f'/api/tickets/{ticket_id}/status',
                      headers=agent_headers,
                      json={'status': 'in_progress'})
    # ticket is 'open', agent can only move to 'assigned' or 'closed'
    assert resp.status_code == 400  # open -> in_progress is invalid

    resp = client.put(f'/api/tickets/{ticket_id}/status',
                      headers=agent_headers,
                      json={'status': 'closed'})
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'closed'


def test_invalid_status_transition(client, agent_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    resp = client.put(f'/api/tickets/{ticket_id}/status',
                      headers=agent_headers,
                      json={'status': 'resolved'})
    assert resp.status_code == 400
    assert 'status' in resp.get_json()['errors']


def test_reopen_within_7_days(client, agent_headers, sample_ticket, app):
    ticket_id = sample_ticket['id']

    # close the ticket
    client.put(f'/api/tickets/{ticket_id}/status',
               headers=agent_headers,
               json={'status': 'closed'})

    # reopen — should succeed (just closed)
    resp = client.put(f'/api/tickets/{ticket_id}/status',
                      headers=agent_headers,
                      json={'status': 'reopened'})
    assert resp.status_code == 200
    assert resp.get_json()['status'] == 'reopened'


def test_reopen_after_7_days_fails(client, agent_headers, sample_ticket, app):
    ticket_id = sample_ticket['id']

    # close the ticket
    client.put(f'/api/tickets/{ticket_id}/status',
               headers=agent_headers,
               json={'status': 'closed'})

    # manually backdate closed_at by 8 days
    with app.app_context():
        ticket = Ticket.query.get(ticket_id)
        ticket.closed_at = datetime.now(timezone.utc) - timedelta(days=8)
        db.session.commit()

    resp = client.put(f'/api/tickets/{ticket_id}/status',
                      headers=agent_headers,
                      json={'status': 'reopened'})
    assert resp.status_code == 400
    assert 'status' in resp.get_json()['errors']


def test_customer_cannot_change_status(client, customer_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    resp = client.put(f'/api/tickets/{ticket_id}/status',
                      headers=customer_headers,
                      json={'status': 'closed'})
    assert resp.status_code == 403
