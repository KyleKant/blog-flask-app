"""
    You need to run init-db again to create the database in the instance folder by command following:
    flask --app blog init-db
    """
import os
import secrets
from flask import Flask, render_template


def create_app(test_config=None):
    # Create and configuration the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='9d25b5816e1e806a349030511bcd87ecc9e5190ed40ec0151f3fd015a0bc372c',
        DATABASE=os.path.join(app.instance_path, 'blog.sqlite'),
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
        pass

    # A single page that says hello

    @app.route('/hello')
    def say_hello():
        return 'Hello there!'

    from . import db
    db.init_app(app)

    from . import auth
    app.register_blueprint(auth.bp)

    # @app.route('/index')
    # def index():
    #     return render_template('index.html')
    from . import blog
    app.register_blueprint(blog.bp)
    app.add_url_rule('/', endpoint='/index')
    return app
