import sqlite3
import MySQLdb
import click
from pprint import pprint
from flask import current_app, g


def get_db():
    if 'db' not in g:
        g.db = MySQLdb.connect(
            host='localhost',
            user='root',
            passwd='1234!@#$',
            db='blog_db',
            # database=current_app.config['DATABASE']
            # current_app.config['DATABASE'],
            # detect_types=sqlite3.PARSE_DECLTYPES,
        )
        # g.db.row_factory = sqlite3.Row
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    cursor = db.cursor()
    with current_app.open_resource('blog_flask_conn.session.sql') as f:
        sqlfile = f.read().decode('utf-8')
        f.close()
    sqlcommand = sqlfile.split(';\r\n')
    # print(sqlcommand)
    for command in sqlcommand:
        try:
            if command.strip() != '':
                cursor.execute(command)
                print(f'command: {command} is executed')
        except IOError:
            print(f'Command is skipped: {IOError}')
    db.commit()
    
        # cursor.executescript(f.read().decode('utf8'))


@click.command('init_db')
def init_db_command():
    """Clear the existing data and create new tables."""
    init_db()
    click.echo('Initialized the database.')


def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
