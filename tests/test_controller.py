def test_show_main_page_returns_200(client):
    response = client.get('/')
    assert response.status_code == 200


def test_show_status_page_returns_200( client):
    response = client.get('/status/')
    assert response.status_code == 200


def test_test_returns_200(client):
    response = client.get('/test/')
    assert response.status_code == 200
