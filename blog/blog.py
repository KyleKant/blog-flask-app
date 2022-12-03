from flask import Blueprint, flash, g, redirect, render_template, url_for, request, session, make_response, abort
import functools
from blog.db import get_db
from datetime import datetime
from blog.auth import login_required

bp = Blueprint('blog', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    if request.method == 'POST':
        print('Delete post')
        delete = request.form
        print(delete)
        if delete == 'delete':
            pass

    db = get_db()
    posts = db.execute(
        '''SELECT p.id, title, body, created, author_id, username FROM post p JOIN users u ON p.author_id = u.id ORDER BY created DESC'''
    ).fetchall()

    response = make_response(render_template('blog/index.html', posts=posts))
    return response


@bp.route('/newpost', methods=('GET', 'POST'))
@login_required
def newpost():
    if request.method == 'POST':
        author_id = session['user_id']
        title = request.form['title']
        content = request.form['content']
        created = datetime.now()
        db = get_db()
        error = None
        if not title:
            error = 'Title is required.'
        elif not content:
            error = 'Content is required.'
        if error is not None:
            flash(error)
        if error == None:
            try:
                db.execute(
                    'INSERT INTO post (author_id, created, title, body) VALUES (?, ?, ?, ?)',
                    (author_id, created, title, content)
                )
                db.commit()
            except db.Error:
                print(db.Error)
            else:
                return redirect(url_for('blog.index'))
    return render_template('blog/newpost.html')


def get_post(id, check_author=True):
    db = get_db()
    post = db.execute(
        'SELECT p.id, title, body, created, author_id, username FROM post p JOIN users u ON p.author_id = u.id WHERE p.id = ?', (
            id,)
    ).fetchone()
    if post is None:
        abort(404, f'Post id {id} doesn\'t exist.')
    if check_author and post['author_id'] != g.user['id']:
        abort(403)
    return post


@bp.route('/post/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
    post = get_post(id)
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['content']
        error = None
        db = get_db()
        if not title:
            error = 'Title is required.'
        elif not body:
            error = 'Content is required.'
        if error is not None:
            flash(error)
        else:
            db.execute(
                'UPDATE post SET title = ?, body = ? WHERE id = ?', (
                    title, body, id)
            )
            db.commit()
            return redirect(url_for('blog.index'))
    return render_template('blog/edit.html', post=post)


@ bp.route('/post/<int:id>/delete', methods=('GET', 'POST'))
@login_required
def delete(id):
    get_post(id)
    db = get_db()
    db.execute(
        'DELETE FROM post WHERE id = ?', (id,)
    )
    db.commit()
    table_post_exist = db.execute(
        'SELECT EXISTS (SELECT * FROM post)'
    ).fetchall()[0][0]
    if not table_post_exist:
        print('post table is empty')
        db.execute(
            'UPDATE sqlite_sequence SET seq = 0 WHERE name = ?', ('post',)
        )
        db.commit()
    else:
        print('post table is not empty')
    return redirect(url_for('blog.index'))


@bp.route('/post/<int:id>/reply', methods=('GET', 'POST'))
@login_required
def reply(id):
    return render_template('blog/reply.html')
