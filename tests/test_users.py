def test_list_users_as_admin(client, admin_headers, customer_headers):
    resp = client.get('/api/users', headers=admin_headers)
    assert resp.status_code == 200
    users = resp.get_json()
    assert isinstance(users, list)
    assert len(users) >= 2  # admin + customer registered by fixtures


def test_list_users_forbidden_for_customer(client, customer_headers):
    resp = client.get('/api/users', headers=customer_headers)
    assert resp.status_code == 403


def test_get_user_by_id(client, admin_headers, customer_headers):
    users = client.get('/api/users', headers=admin_headers).get_json()
    customer = next(u for u in users if u['role'] == 'customer')
    resp = client.get(f'/api/users/{customer["id"]}', headers=admin_headers)
    assert resp.status_code == 200
    assert resp.get_json()['id'] == customer['id']


def test_get_user_not_found(client, admin_headers):
    resp = client.get('/api/users/99999', headers=admin_headers)
    assert resp.status_code == 404


def test_update_user_role(client, admin_headers, customer_headers):
    users = client.get('/api/users', headers=admin_headers).get_json()
    customer = next(u for u in users if u['role'] == 'customer')
    resp = client.put(f'/api/users/{customer["id"]}',
                      headers=admin_headers,
                      json={'role': 'agent'})
    assert resp.status_code == 200
    assert resp.get_json()['role'] == 'agent'


def test_list_agents(client, admin_headers, agent_headers):
    resp = client.get('/api/agents', headers=admin_headers)
    assert resp.status_code == 200
    agents = resp.get_json()
    assert all(a['role'] == 'agent' for a in agents)


def test_agent_tickets(client, admin_headers, agent_headers):
    users = client.get('/api/users', headers=admin_headers).get_json()
    agent = next(u for u in users if u['role'] == 'agent')
    resp = client.get(f'/api/agents/{agent["id"]}/tickets', headers=admin_headers)
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_update_availability(client, agent_headers, admin_headers):
    users = client.get('/api/users', headers=admin_headers).get_json()
    agent = next(u for u in users if u['role'] == 'agent')
    resp = client.put(f'/api/agents/{agent["id"]}/availability',
                      headers=agent_headers,
                      json={'availability_status': 'busy'})
    assert resp.status_code == 200
    assert resp.get_json()['availability_status'] == 'busy'


def test_update_availability_invalid_value(client, agent_headers, admin_headers):
    users = client.get('/api/users', headers=admin_headers).get_json()
    agent = next(u for u in users if u['role'] == 'agent')
    resp = client.put(f'/api/agents/{agent["id"]}/availability',
                      headers=agent_headers,
                      json={'availability_status': 'dancing'})
    assert resp.status_code == 400
