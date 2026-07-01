def test_add_public_comment_as_customer(client, customer_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    resp = client.post(f'/api/tickets/{ticket_id}/comments',
                       headers=customer_headers,
                       json={'content': 'I still have the issue.', 'is_internal': False})
    assert resp.status_code == 201
    data = resp.get_json()
    assert data['is_internal'] is False


def test_add_internal_comment_as_agent(client, agent_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    resp = client.post(f'/api/tickets/{ticket_id}/comments',
                       headers=agent_headers,
                       json={'content': 'Internal note: check the server logs.', 'is_internal': True})
    assert resp.status_code == 201
    assert resp.get_json()['is_internal'] is True


def test_customer_cannot_post_internal_comment(client, customer_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    resp = client.post(f'/api/tickets/{ticket_id}/comments',
                       headers=customer_headers,
                       json={'content': 'Trying to post internal.', 'is_internal': True})
    assert resp.status_code == 403


def test_customer_cannot_see_internal_comments(client, customer_headers, agent_headers, sample_ticket):
    ticket_id = sample_ticket['id']
    # agent posts internal comment
    client.post(f'/api/tickets/{ticket_id}/comments',
                headers=agent_headers,
                json={'content': 'Internal only note here.', 'is_internal': True})
    # customer posts public comment
    client.post(f'/api/tickets/{ticket_id}/comments',
                headers=customer_headers,
                json={'content': 'A public reply from the customer.', 'is_internal': False})

    # customer fetches comments — should not see internal
    resp = client.get(f'/api/tickets/{ticket_id}/comments', headers=customer_headers)
    assert resp.status_code == 200
    comments = resp.get_json()
    assert all(not c['is_internal'] for c in comments)
    assert len(comments) == 1
