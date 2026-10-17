import click
from flask.cli import with_appcontext
from werkzeug.security import generate_password_hash
from extensions import db
from models import User


@click.command('init-db')
@with_appcontext
def init_db():
    """Create all tables."""
    db.create_all()
    click.echo('Database ready.')


@click.command('create-user')
@with_appcontext
def create_user():
    """Create a teacher or CR account."""
    username = click.prompt('Username')
    if User.query.filter_by(username=username).first():
        raise click.ClickException('Username already exists.')
    name = click.prompt('Full name')
    role = click.prompt('Role', type=click.Choice(['teacher', 'cr']))
    pw = click.prompt('Password', hide_input=True, confirmation_prompt=True)
    db.create_all()
    db.session.add(User(username=username, name=name, role=role, pw=generate_password_hash(pw)))
    db.session.commit()
    click.echo('User created.')


def register_cli(app):
    app.cli.add_command(init_db)
    app.cli.add_command(create_user)
