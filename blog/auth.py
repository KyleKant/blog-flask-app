import functools
import os
from flask import Blueprint, flash, g, redirect, render_template, request, session, url_for, make_response
from werkzeug.security import check_password_hash, generate_password_hash
from flask_mail import Message
from datetime import datetime
from blog.db import get_db
from blog import mail
from blog.token import generate_confirmation_token, confirm_token
from pprint import pprint

bp = Blueprint('auth', __name__, url_prefix='/auth')


@bp.route('/register', methods=('GET', 'POST'))
def register_user():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        password_confirm = request.form['passwordConfirm']
        registered_at = datetime.now()
        confirmed = False
        db = get_db()
        cursor = db.cursor()
        error = None
        if not username:
            error = 'Username is required.'
        elif not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif password != password_confirm:
            error = 'Password doesn\'t match.'
        if error == None:
            token = generate_confirmation_token(email=email)
            confirm_url = url_for('auth.confirmed_email',
                                  token=token, _external=True)
            with open(os.path.join(os.path.dirname(__file__),
                                   'templates\\auth\\verification_email_subject.txt'), "r") as f:
                subject = f.read()
                f.close()
            with open(os.path.join(os.path.dirname(__file__), 'templates\\auth\\confirm_email.html'), 'r') as f:
                message = f.read()
                f.close()
            message_body = render_template(
                'auth/confirm_email.html', username=username, confirm_url=confirm_url)
            msg = Message(subject, recipients=[email], html=message_body,)
            mail.send(msg)

            try:
                cursor.execute(
                    'INSERT INTO users (username, email, password, registered_at, confirmed) VALUES (%s, %s, %s, %s, %s)',
                    (username, email, generate_password_hash(
                        password), registered_at, confirmed)
                )
                db.commit()
            except db.IntegrityError:
                error = f'User have {email} or {username} is already registered.'
            else:
                print('user table has been updated.')
                return redirect(url_for('auth.send_confirmation_email'))
        flash(error)
    return render_template('auth/register_user.html')


@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor(0)
        error = None
        cursor.execute(
            'SELECT * FROM users WHERE username = %s', (username,)
        )
        user_value_dict = cursor.fetchone()
        user_key_dict = ('id', 'username', 'email', 'password',
                         'registered_at', 'confirmed', 'confirmed_at')
        try:
            user = dict(zip(user_key_dict, user_value_dict))
        except TypeError:
            print('Users table is empty!')
            user = None
        if user is None:
            error = 'Incorrect username or not exists.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'
        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('blog.index'))
        flash(error)
    return render_template('auth/login.html')


@bp.before_app_request
def load_logged_in_user():
    # session.clear()
    user_id = session.get('user_id')
    if user_id is None:
        g.user = None
    else:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE id =%s', (user_id,)
        )
        user_value_dict = cursor.fetchone()
        try:
            user_key_dict = ('id', 'username', 'email', 'password',
                             'registered_at', 'confirmed', 'confirmed_at')
            g.user = dict(zip(user_key_dict, user_value_dict))
        except TypeError:
            g.user = None
            print('Database is empty!')


def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))
        return view(**kwargs)
    return wrapped_view


@bp.route('/logout', methods=('GET', 'POST'))
def logout():
    session.clear()
    return redirect(url_for('blog.index'))


@bp.route('/send_confirmation_email', methods=('GET', 'POST'))
def send_confirmation_email():
    return render_template('auth/send_confirmation_email.html')


@bp.route('/confirmed_email/<token>')
def confirmed_email(token):
    error = None
    email = confirm_token(token=token)
    if email is False:
        error = 'The confirmation link is invalid or has expried.'
    else:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE email=%s',
            (email,)
        )
        user_value_dict = cursor.fetchone()
        user_key_dict = ('id', 'username', 'email', 'password',
                         'registered_at', 'confirmed', 'confirmed_at')
        try:
            user = dict(zip(user_key_dict, user_value_dict))
        except TypeError:
            user = None
            print(f'Email {email} is not exists.')
        if user['confirmed']:
            flash(f'Email {email} already comnfirmed. Please login.')
        else:
            user['confirmed'] = True
            user['confirmed_at'] = datetime.now()
            cursor.execute(
                'UPDATE users SET confirmed=%s, confirmed_at=%s WHERE email=%s',
                (user['confirmed'], user['confirmed_at'], user['email'])
            )
            db.commit()
    if error is not None:
        flash(error)
    else:
        flash(f'Email {email} has been confirmed.')
    return redirect(url_for('auth.unconfirmed_email'))


@bp.route('/resend_verification_email', methods=('GET', 'POST'))
@login_required
def resend_verification_email():
    token = generate_confirmation_token(g.user['email'])
    confirm_url = url_for(
        'auth.confirmed_email', token=token, _external=True)
    with open(os.path.join(os.path.dirname(__file__), 'templates\\auth\\verification_email_subject.txt'), 'r') as f:
        subject = f.read()
        f.close()
    with open(os.path.join(os.path.dirname(__file__), 'templates\\auth\\confirm_email.html'), 'r') as f:
        message = f.read()
        f.close()
    message_html = render_template(
        'auth/confirm_email.html', username=g.user['username'], confirm_url=confirm_url)
    msg = Message(subject=subject, recipients=[
                  g.user['email'],], html=message_html)
    mail.send(msg)
    flash('A new confirmation email has been sent to your email.')
    return redirect(url_for('auth.unconfirmed_email'))


@bp.route('/unconfirmed_email', methods=('GET', 'POST'))
@login_required
def unconfirmed_email():
    if g.user['confirmed']:
        return redirect(url_for('blog.index'))
    flash('Please confirm your account.')
    return render_template('auth/unconfirmed_email.html')


def check_confirmed_email(func):
    @functools.wraps(func)
    def decorated_func(*args, **kwargs):
        if g.user['confirmed'] is False:
            flash('Please confirm your account.')
            return redirect(url_for('auth.unconfirmed_email'))
        return func(*args, **kwargs)
    return decorated_func


@bp.route('/reset_password', methods=('GET', 'POST'))
def reset_password():
    if request.method == 'POST':
        email = request.form['email']
        token = generate_confirmation_token(email=email)
        confirm_url = url_for('auth.confirmed_reset_password',
                              token=token, _external=True)
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            'SELECT * FROM users WHERE email=%s',
            (email,)
        )
        user_value_dict = cursor.fetchone()
        user_key_dict = ('id', 'username', 'email', 'password',
                         'registered_at', 'confirmed', 'confirmed_at')
        try:
            user = dict(zip(user_key_dict, user_value_dict))
        except TypeError:
            user = None
        if user == None:
            flash(f'Email address: {email} is not exists.')
        else:
            with open(os.path.join(
                os.path.dirname(__file__),
                'templates/auth/reset_password/reset_password_subject.txt'
            ), 'r') as f:
                subject = f.read()
                f.close()
            message_html = render_template(
                'auth/reset_password/reset_password_email.html',
                confirm_url=confirm_url,
                email=email,
                username=user['username']
            )
            msg = Message(subject=subject, recipients=[
                          email,], html=message_html)
            mail.send(msg)
            return redirect(url_for('auth.send_reset_password_email'))
    return render_template('auth/reset_password/reset_password.html')


@bp.route('send_reset_password_email', methods=('GET', 'POST'))
def send_reset_password_email():
    return render_template('auth/reset_password/send_reset_password_email.html')


@bp.route('/reset_password/confirmed_reset_password/<token>', methods=('GET', 'POST'))
def confirmed_reset_password(token):
    error = None
    email = confirm_token(token)
    if email == False:
        error = 'expried'
        flash('Link has expried')
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT * FROM users WHERE email=%s',
        (email,)
    )
    user_value_dict = cursor.fetchone()
    user_key_dict = ('id', 'username', 'email', 'password',
                     'register_at', 'confirmed', 'confirmed_at')
    try:
        user = dict(zip(user_key_dict, user_value_dict))
    except TypeError:
        user = None
    if user == None:
        flash(f'Email address: {email} is not exists.')
    elif error == None:
        return redirect(url_for('auth.set_new_password'))
    return redirect(url_for('auth.reset_password'))


@bp.route('/set_new_password', methods=('GET', 'POST'))
def set_new_password():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['new_password']
        repeat_password = request.form['repeat_new_password']
        error = None
        if not email:
            error = 'Email is required.'
        elif not password:
            error = 'Password is required.'
        elif not repeat_password:
            error = 'Repeat password is required.'
        elif password != repeat_password:
            error = 'Password and repeat password is not match.'
        if error == None:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                'UPDATE users SET password=%s WHERE email=%s',
                (generate_password_hash(password=password), email)
            )
            db.commit()
            return redirect(url_for('auth.login'))
        flash(error)
    return render_template('auth/reset_password/set_new_password.html')


@bp.route('/my_accounts', methods=('GET', 'POST'))
@login_required
@check_confirmed_email
def my_account():
    db = get_db()
    cursor = db.cursor()
    cursor.execute(
        'SELECT COUNT(id) FROM post WHERE author_id=%s',
        (g.user['id'],)
    )
    post_num = cursor.fetchone()[0]
    cursor.execute(
        'SELECT COUNT(id) FROM reply WHERE created_by=%s',
        (g.user['username'],)
    )
    reply_num = cursor.fetchone()[0]
    cursor.execute(
        'SELECT * FROM post WHERE author_id=%s ORDER BY created DESC limit 2',
        (g.user['id'],)
    )
    five_first_post_list = cursor.fetchall()
    five_first_post_key_dict = (
        'id', 'author_id', 'created', 'title', 'body', 'votes')
    five_first_post = []
    try:
        for five_first_post_value_dict in five_first_post_list:
            five_first_post.append(dict(
                zip(five_first_post_key_dict, five_first_post_value_dict)))
    except TypeError:
        five_first_post = None
    pprint(five_first_post)
    return render_template('auth/my_account.html', post_num=post_num, reply_num=reply_num, five_first_post=five_first_post)


@bp.route('/change_password', methods=('GET', 'POST'))
@login_required
@check_confirmed_email
def change_password():
    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        error = None
        if not old_password:
            error = 'Old password is required.'
        elif not new_password:
            error = 'New password is required.'
        if error == None:
            db = get_db()
            cursor = db.cursor()
            cursor.execute(
                'SELECT * FROM users WHERE id=%s',
                (g.user['id'],)
            )
            user_value_dict = cursor.fetchone()
            user_key_dict = ('id', 'username', 'email', 'password',
                             'registered_at', 'confirmed', 'confirmed_at')
            try:
                user = dict(zip(user_key_dict, user_value_dict))
            except TypeError:
                user = None
                print('User is not exists.')
            if user:
                if not check_password_hash(user['password'], old_password):
                    flash('The old password is not true, please type password again.')
                else:
                    cursor.execute(
                        'UPDATE users SET password=%s WHERE id=%s',
                        (generate_password_hash(new_password), g.user['id'],)
                    )
                    db.commit()
                    print(f'Password has been changed to {new_password}')
                    return redirect(url_for('auth.my_account'))
    return render_template('auth/change_password/change_password.html')
