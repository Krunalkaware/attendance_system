from flask import Flask
from config import Config
from extensions import db, csrf, login_manager, migrate
from routes import register_blueprints
from cli import register_cli
import models  # noqa: F401  (registers tables with SQLAlchemy)


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    csrf.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    migrate.init_app(app, db)
    register_blueprints(app)
    register_cli(app)
    return app


app = create_app()

if __name__ == '__main__':
    app.run(debug=True)
