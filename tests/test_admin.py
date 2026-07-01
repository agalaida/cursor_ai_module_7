def test_dashboard_returns_metrics(client, admin_headers, sample_ticket):
    resp = client.get('/api/admin/dashboard', headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'tickets_by_status' in data
    assert 'total_tickets' in data
    assert data['total_tickets'] >= 1


def test_dashboard_forbidden_for_customer(client, customer_headers):
    resp = client.get('/api/admin/dashboard', headers=customer_headers)
    assert resp.status_code == 403


def test_sla_report(client, admin_headers):
    resp = client.get('/api/admin/reports/sla', headers=admin_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert 'compliant' in data
    assert 'compliance_rate' in data


def test_export_csv(client, admin_headers, sample_ticket):
    resp = client.post('/api/admin/reports/export', headers=admin_headers)
    assert resp.status_code == 200
    assert 'text/csv' in resp.content_type
    content = resp.data.decode()
    assert 'ticket_number' in content
    assert sample_ticket['ticket_number'] in content
