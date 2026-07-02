def _ticket_payload(**overrides):
    payload = {
        'subject': 'Valid subject line here',
        'description': 'This description is long enough to pass validation rules easily.',
        'customer_email': 'alice@example.com',
    }
    payload.update(overrides)
    return payload


def test_subject_at_minimum_length_boundary(client, customer_headers):
    """TC-201-style: exactly 5 chars (the schema minimum) must be accepted."""
    resp = client.post('/api/tickets', headers=customer_headers,
                       json=_ticket_payload(subject='Fixit'))
    assert resp.status_code == 201


def test_subject_below_minimum_length_boundary(client, customer_headers):
    resp = client.post('/api/tickets', headers=customer_headers,
                       json=_ticket_payload(subject='Fix'))
    assert resp.status_code == 400


def test_description_at_maximum_length_boundary(client, customer_headers):
    resp = client.post('/api/tickets', headers=customer_headers,
                       json=_ticket_payload(description='A' * 5000))
    assert resp.status_code == 201


def test_description_above_maximum_length_boundary(client, customer_headers):
    resp = client.post('/api/tickets', headers=customer_headers,
                       json=_ticket_payload(description='A' * 5001))
    assert resp.status_code == 400


def test_unicode_characters_in_description(client, customer_headers):
    """Non-Latin scripts and emoji must round-trip untouched (sanitize only escapes HTML)."""
    text = 'Проблема с принтером 🖨️ не печатает документы совсем, помогите разобраться.'
    resp = client.post('/api/tickets', headers=customer_headers,
                       json=_ticket_payload(description=text))
    assert resp.status_code == 201
    assert resp.get_json()['description'] == text


def test_malformed_json_body_returns_400(client, customer_headers):
    headers = dict(customer_headers)
    headers['Content-Type'] = 'application/json'
    resp = client.post('/api/tickets', headers=headers, data='{not valid json')
    assert resp.status_code == 400


def test_create_ticket_omitting_optional_fields_uses_defaults(client, customer_headers):
    resp = client.post('/api/tickets', headers=customer_headers, json={
        'subject': 'Valid subject line here',
        'description': 'This description is long enough to pass validation rules easily.',
        'customer_email': 'alice@example.com',
    })
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['priority'] == 'medium'
    assert data['category'] == 'general'
