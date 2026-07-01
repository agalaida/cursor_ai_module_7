def _create_agent(client):
    client.post('/api/auth/register', json={
        'name': 'Agent Dave', 'email': 'dave@example.com',
        'password': 'password123', 'role': 'agent',
    })
    from app.models.user import User
    with client.application.app_context():
        agent = User.query.filter_by(email='dave@example.com').first()
        return agent.id


def test_admin_can_assign_ticket(client, admin_headers, sample_ticket):
    agent_id = _create_agent(client)
    ticket_id = sample_ticket['id']
    resp = client.post(f'/api/tickets/{ticket_id}/assign',
                       headers=admin_headers,
                       json={'agent_id': agent_id})
    assert resp.status_code == 200
    data = resp.get_json()
    assert data['assigned_to_id'] == agent_id
    assert data['status'] == 'assigned'


def test_reassign_ticket(client, admin_headers, sample_ticket):
    agent_id = _create_agent(client)
    ticket_id = sample_ticket['id']

    client.post(f'/api/tickets/{ticket_id}/assign',
                headers=admin_headers,
                json={'agent_id': agent_id})

    # register second agent and reassign
    client.post('/api/auth/register', json={
        'name': 'Agent Eve', 'email': 'eve@example.com',
        'password': 'password123', 'role': 'agent',
    })
    with client.application.app_context():
        from app.models.user import User
        eve = User.query.filter_by(email='eve@example.com').first()
        eve_id = eve.id

    resp = client.post(f'/api/tickets/{ticket_id}/assign',
                       headers=admin_headers,
                       json={'agent_id': eve_id})
    assert resp.status_code == 200
    assert resp.get_json()['assigned_to_id'] == eve_id


def test_non_admin_cannot_assign(client, agent_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    resp = client.post(f'/api/tickets/{ticket_id}/assign',
                       headers=agent_headers,
                       json={'agent_id': 1})
    assert resp.status_code == 403
