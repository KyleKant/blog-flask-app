from flask import Blueprint, flash, g, redirect, render_template, url_for, request, session, make_response, abort
import functools
from blog.db import get_db
from datetime import datetime
from blog.auth import login_required, check_confirmed_email
from flaskext.markdown import Markdown
bp = Blueprint('blog', __name__)


@bp.route('/', methods=('GET', 'POST'))
def index():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        '''SELECT p.id, title, body, created, author_id, username FROM post p JOIN users u ON p.author_id = u.id ORDER BY created DESC'''
    )
    posts_list = cursor.fetchall()
    posts = []
    posts_key_dict = ('id', 'title', 'body', 'created',
                      'author_id', 'username')
    for posts_value_dict in posts_list:
        posts.append(dict(zip(posts_key_dict, posts_value_dict)))
    response = make_response(render_template('blog/index.html', posts=posts))
    return response


@bp.route('/<int:id>/<title>', methods=('GET', 'POST'))
@login_required
@check_confirmed_email
def post(id, title):
    post = get_post(id)
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT * FROM reply'
    )
    replys_tuple = cursor.fetchall()
    reply_key_dict = ('id', 'created_by', 'created_at', 'post_id', 'reply')
    replys = []
    for reply_value_dict in replys_tuple:
        replys.append(dict(zip(reply_key_dict, reply_value_dict)))
    return render_template('blog/post.html', post=post, replys=replys)


@bp.route('/newpost', methods=('GET', 'POST'))
@login_required
@check_confirmed_email
def newpost():
    if request.method == 'POST':
        author_id = session['user_id']
        title = request.form['title']
        content = request.form['content']
        created = datetime.now()
        votes = 0
        db = get_db()
        cursor = db.cursor()
        error = None
        if not title:
            error = 'Title is required.'
        elif not content:
            error = 'Content is required.'
        if error is not None:
            flash(error)
        if error == None:
            try:
                cursor.execute(
                    'INSERT INTO post (author_id, created, title, body, votes) VALUES (%s, %s, %s, %s, %s)',
                    (author_id, created, title, content, votes)
                )
                db.commit()
            except db.Error:
                print(db.Error)
            else:
                return redirect(url_for('blog.index'))
    return render_template('blog/newpost.html')


def get_post(id, check_author=True):
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT p.id, title, body, created, author_id, username, votes FROM post p JOIN users u ON p.author_id = u.id WHERE p.id = %s',
        (id,)
    )
    post_value_dict = cursor.fetchone()
    post_key_dict = ('id', 'title', 'body', 'created',
                     'author_id', 'username', 'votes')
    try:
        post = dict(zip(post_key_dict, post_value_dict))
    except TypeError as err:
        print('Table post is empty.')
        post = None
    if post is None:
        abort(404, f'Post id {id} doesn\'t exist.')
    # if check_author and post['author_id'] != g.user['id']:
    #     abort(403)
    return post


def get_reply(reply_id, post_id, check_author=True):
    # post = get_post(post_id)
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT r.id, reply, created_by, created_at, post_id FROM reply r JOIN users u ON r.created_by = u.username JOIN post p ON r.post_id = p.id WHERE r.id = %s',
        (reply_id,)
    )
    reply_value_dict = cursor.fetchone()

    reply_key_dict = ('id', 'reply', 'created_by', 'created_at', 'post_id')
    try:
        reply = dict(zip(reply_key_dict, reply_value_dict))
    except TypeError:
        print('Reply table is empty.')
        reply = None
    if reply is None:
        abort(404, f'Reply id {reply_id} doesn\'t exists.')
    if check_author and reply['created_by'] != g.user['username']:
        abort(403)
    return reply


@bp.route('/post/<int:id>/edit', methods=('GET', 'POST'))
@login_required
def edit(id):
    post = get_post(id)
    if request.method == 'POST':
        title = request.form['title']
        body = request.form['content']
        error = None
        db = get_db()
        cursor = db.cursor()
        if not title:
            error = 'Title is required.'
        elif not body:
            error = 'Content is required.'
        if error is not None:
            flash(error)
        else:
            cursor.execute(
                'UPDATE post SET title = %s, body = %s WHERE id = %s', (
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
    cursor = db.cursor()
    cursor.execute(
        'DELETE FROM post WHERE id = %s', (id,)
    )
    db.commit()
    cursor.execute(
        'SELECT EXISTS (SELECT * FROM post)'
    )
    table_is_empty = cursor.fetchall()[0][0]
    if not table_is_empty:
        print('post table is empty')
        db.execute(
            'ALTER TABLE post AUTO_INCREMENT = 1'
        )
        db.commit()
    else:
        print('post table is not empty')
    return redirect(url_for('blog.index'))


@bp.route('/post/<int:id>/reply', methods=('GET', 'POST'))
@login_required
def reply(id):
    post = get_post(id)
    if request.method == 'POST':
        reply = request.form['reply']
        created_by = g.user['username']
        created_at = datetime.now()
        post_id = id
        error = None
        if not reply:
            error = 'Reply is required.'
        elif error is None:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                'INSERT INTO reply (created_by, created_at, post_id, reply) VALUES (%s, %s, %s, %s)',
                (created_by, created_at, post_id, reply)
            )
            db.commit()
            return redirect(url_for('blog.index'))
        flash(error)
    return render_template('blog/reply.html', post=post)


def get_my_post(author_id):
    my_posts = []
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT * FROM post WHERE author_id=%s',
        (g.user['id'],)
    )
    my_post_value_list = cursor.fetchall()
    my_post_key_dict = ('id', 'author_id', 'created', 'title', 'body', 'votes')
    try:
        for my_post_value_dict in my_post_value_list:
            my_posts.append(dict(zip(my_post_key_dict, my_post_value_dict)))
    except TypeError:
        my_posts = None
    return my_posts


@bp.route('/<username>/post', methods=('GET', 'POST'))
@login_required
def my_post(username):
    author_id = g.user['id']
    my_posts = get_my_post(author_id=author_id)
    return render_template('blog/my_account/my_post.html', my_posts=my_posts)


@bp.route('/post_vote/<id>', methods=('GET', 'POST'))
def post_vote(id):
    post = get_post(id)
    vote = post['votes']
    if request.method == 'POST':
        vote += 1
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'UPDATE post SET votes=%s WHERE id=%s',
            (vote, id)
        )
        db.commit()
    return redirect(url_for('blog.post', id=id, title=post['title']))
