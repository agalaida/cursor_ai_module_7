def test_ticket_subject_too_short(client, customer_headers):
    resp = client.post('/api/tickets', headers=customer_headers, json={
        'subject': 'Hi',
        'description': 'This description is long enough to pass validation.',
        'customer_email': 'alice@example.com',
    })
    assert resp.status_code == 400
    assert 'subject' in resp.get_json()['errors']


def test_ticket_description_too_short(client, customer_headers):
    resp = client.post('/api/tickets', headers=customer_headers, json={
        'subject': 'Valid subject line here',
        'description': 'Too short',
        'customer_email': 'alice@example.com',
    })
    assert resp.status_code == 400
    assert 'description' in resp.get_json()['errors']


def test_ticket_invalid_priority(client, customer_headers):
    resp = client.post('/api/tickets', headers=customer_headers, json={
        'subject': 'Valid subject line here',
        'description': 'This description is long enough to pass validation rules.',
        'priority': 'super_urgent',
        'customer_email': 'alice@example.com',
    })
    assert resp.status_code == 400
    assert 'priority' in resp.get_json()['errors']


def test_ticket_invalid_customer_email(client, customer_headers):
    resp = client.post('/api/tickets', headers=customer_headers, json={
        'subject': 'Valid subject line here',
        'description': 'This description is long enough to pass validation rules.',
        'customer_email': 'not-valid-email',
    })
    assert resp.status_code == 400
    assert 'customer_email' in resp.get_json()['errors']


def test_priority_update_requires_reason(client, agent_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    resp = client.put(f'/api/tickets/{ticket_id}/priority',
                      headers=agent_headers,
                      json={'priority': 'urgent'})
    assert resp.status_code == 400
    assert 'reason' in resp.get_json()['errors']


def test_status_update_invalid_value(client, agent_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    resp = client.put(f'/api/tickets/{ticket_id}/status',
                      headers=agent_headers,
                      json={'status': 'flying'})
    assert resp.status_code == 400
