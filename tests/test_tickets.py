def test_create_ticket_success(client, customer_headers):
    resp = client.post('/api/tickets', headers=customer_headers, json={
        'subject': 'My printer is broken',
        'description': 'The printer does not respond and shows a red light.',
        'priority': 'medium',
        'category': 'technical',
        'customer_email': 'alice@example.com',
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['status'] == 'open'
    assert data['ticket_number'].startswith('TICK-')


def test_create_ticket_without_auth(client):
    resp = client.post('/api/tickets', json={
        'subject': 'No auth ticket',
        'description': 'Should be rejected because there is no auth token.',
        'customer_email': 'anon@example.com',
    })
    assert resp.status_code == 401


def test_get_ticket_by_owner(client, customer_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    resp = client.get(f'/api/tickets/{ticket_id}', headers=customer_headers)
    assert resp.status_code == 200
    assert resp.get_json()['id'] == ticket_id


def test_get_ticket_not_found(client, admin_headers):
    resp = client.get('/api/tickets/99999', headers=admin_headers)
    assert resp.status_code == 404


def test_list_tickets_customer_sees_only_own(client, customer_headers, sample_ticket):
    resp = client.get('/api/tickets', headers=customer_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    for t in data['tickets']:
        assert t['customer_email'] == 'alice@example.com'


def test_delete_ticket_admin(client, admin_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    resp = client.delete(f'/api/tickets/{ticket_id}', headers=admin_headers)
    assert resp.status_code == 200


def test_delete_ticket_forbidden_for_agent(client, agent_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    resp = client.delete(f'/api/tickets/{ticket_id}', headers=agent_headers)
    assert resp.status_code == 403
