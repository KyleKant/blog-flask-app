"""
    You need to run init-db again to create the database in the instance folder by command following:
    flask --app blog init-db
    """
import os
import secrets
from flask import Flask, render_template
from flask_simplemde import SimpleMDE
from flaskext.markdown import Markdown
from flask_gravatar import Gravatar
from flask_mail import Mail, Message

mail = Mail()


def create_app(test_config=None):
    # Create and configuration the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='9d25b5816e1e806a349030511bcd87ecc9e5190ed40ec0151f3fd015a0bc372c',
        # DATABASE=os.path.join(app.instance_path, 'blog_db.sql'),
    )
    if test_config == None:
        # Load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # Load the test config, if it passed in
        app.config.from_mapping(test_config)
    # Ensure that instance folder exits
    try:
        os.makedirs(app.instance_path)
    except OSError:
        print('Can\'t create instance dir')

    # # config SimpleMDE
    # app.config['SIMPLEMDE_IS_IIFE'] = True
    # app.config['SIMPLEMDE_USE_CDN'] = True
    # SimpleMDE(app)

    # config Markdown
    Markdown(app, extensions=['attr_list', 'codehilite', 'fenced_code'])

    # Config Gravatar
    app.config['GRAVATAR_SIZE'] = 50
    app.config['GRAVATAR_RATING'] = 'g'
    app.config['GRAVATAR_DEFAULT'] = 'retro'
    app.config['GRAVATAR_FORCE_DEFAULT'] = False
    app.config['GRAVATAR_FORCE_LOWER'] = False
    app.config['GRAVATAR_USE_SSL'] = False
    app.config['GRAVATAR_BASE_URL'] = None
    # Initialize Gravatar
    gravatar = Gravatar(app)

    # config security password
    if 'SECURITY_PASSWORD_SALT' not in app.config:
        app.config['SECURITY_PASSWORD_SALT'] = app.config['SECRET_KEY']

    # Config Email Server
    app.config['MAIL_SERVER'] = 'smtp.gmail.com'
    app.config['MAIL_PORT'] = 587
    app.config['MAIL_USERNAME'] = 'onhanam1234@gmail.com'
    app.config['MAIL_PASSWORD'] = 'qwcpfcsahnzfpyve'
    app.config['MAIL_USE_TLS'] = True
    app.config['MAIL_USE_SSL'] = False
    app.config['MAIL_DEFAULT_SENDER'] = 'onhanam1234@gmail.com'

    # A single page that says hello

    @app.route('/hello')
    def say_hello():
        return 'Hello there!'

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)
    mail.init_app(app)
    # @app.route('/index')
    # def index():
    #     return render_template('index.html')
    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='/index')
    return app
