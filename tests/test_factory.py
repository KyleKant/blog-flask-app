from blog import create_app

# print(create_app({'TESTING': True}).testing)


def test_config():
    assert not create_app().testing
    assert create_app({'TESTING': True}).testing


def test_hello(client):
    response = client.get('/hello')
    assert response.data == b'Hello there!'
