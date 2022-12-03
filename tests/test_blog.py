import pytest
from blog.db import get_db
from flask import g, session, request


def test_get_post(client, auth):
    response = client.get('/')
    assert response.status_code == 200
    assert b'Login' in response.data
    assert b'Register' in response.data

    auth.login()
    response = client.get('/')
    assert response.status_code == 200
    assert b'Log Out' in response.data
    assert b'user' in response.data
    assert b'example title' in response.data
    assert b'example\nbody' in response.data
    assert b'by user on 2022-11-26' in response.data
    assert b'href="/post/1/edit"' in response.data
    assert b'href="/post/1/reply"' in response.data
    assert b'href="/newpost"' in response.data


@pytest.mark.parametrize(
    ('path'),
    (('/newpost'), ('/post/1/edit'), ('post/1/delete')),
)
def test_login_required(client, path):
    response = client.get(path)
    assert response.status_code == 302
    assert response.headers['Location'] == '/auth/login'


def test_author_required(client, auth, app):
    # Change post author to another user
    with app.app_context():
        db = get_db()
        db.execute(
            'UPDATE post SET author_id = 2 WHERE id = 1'
        )
        db.commit()
    auth.login()
    # current user can not modify other user's post
    assert client.post('/post/1/edit').status_code == 403
    assert client.post('/post/1/delete').status_code == 403
    # current user can not see edit link
    assert b'href="/post/1/edit"' not in client.get('/').data


@pytest.mark.parametrize(
    ('path'),
    (('/post/2/edit'), ('/post/2/delete')),
)
def test_not_exists_required(client, auth, path):
    auth.login()
    assert client.get(path).status_code == 404


def test_get_newpost(client, auth, app):
    response = client.get('/newpost')
    assert response.headers['Location'] == '/auth/login'

    auth.login()
    response = client.get(
        '/newpost')
    assert response.status_code == 200
    assert b'user' in response.data
    assert b'Log Out' in response.data
    assert b'New Post' in response.data
    assert b'Title' in response.data
    assert b'Content' in response.data

    response = client.post(
        '/newpost',
        data={'title': 'title', 'content': 'content\ncontent'}
    )
    assert response.status_code == 302
    assert response.headers['Location'] == '/'
    with app.app_context():
        db = get_db()
        count = db.execute(
            'SELECT COUNT(id) FROM post'
        ).fetchone()[0]
        assert count == 2
        post = db.execute(
            'SELECT * FROM post WHERE id = 2'
        ).fetchone()
        assert post['title'] == 'title'
        assert post['body'] == 'content\ncontent'


def test_edit(client, auth, app):
    auth.login()
    response = client.get('/post/1/edit')
    assert response.status_code == 200
    assert b'example title' in response.data
    assert b'example\nbody' in response.data
    assert b'href="/"' in response.data
    title = 'test example title'
    content = 'test\nexample\nbody'
    response = client.post(
        '/post/1/edit',
        data={'title': title, 'content': content}
    )
    assert response.status_code == 302
    assert response.headers['Location'] == '/'
    with app.app_context():
        db = get_db()
        post = db.execute(
            'SELECT * FROM post WHERE id = 1'
        ).fetchone()
        assert post['title'] == 'test example title'
        assert post['body'] == 'test\nexample\nbody'


@pytest.mark.parametrize(
    ('path'),
    (('/newpost'), ('/post/1/edit')),
)
def test_create_update_validate(client, auth, path):
    auth.login()
    with client:
        response = client.post(
            path, data={'title': '', 'content': ''})
        assert b'Title is required' in response.data
        response = client.post(
            path,
            data={'title': 'a', 'content': ''}
        )
        assert b'Content is required.' in response.data


def test_delete(client, auth, app):
    auth.login()
    response = client.post('/post/1/delete')
    assert response.headers['Location'] == '/'
    with app.app_context():
        db = get_db()
        post = db.execute(
            'SELECT * FROM post WHERE id = 1'
        ).fetchone()
        assert post is None
