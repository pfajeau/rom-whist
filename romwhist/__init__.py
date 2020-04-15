"""
App init module

@author: Philippe Fajeau
"""

from flask import Flask, redirect, url_for, render_template
from flask_login import LoginManager
import logging
import logging.handlers
from .extensions import *
from flask_bootstrap import Bootstrap


app = Flask(__name__, instance_relative_config=True, template_folder="ui/templates", static_folder="ui/static")

from .routes import *

def create_app():
    login_manager = LoginManager()

    Bootstrap(app)

    app.config.from_pyfile("config.py")

    # logging
    handler = logging.handlers.RotatingFileHandler(app.config["LOG_FILE"], maxBytes=app.config["LOG_SIZE"])
    handler.setLevel(app.config["LOG_LEVEL"])
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s [%(pathname)s at %(lineno)s]: %(message)s", "%Y-%m-%d %H:%M:%S"))
    app.logger.addHandler(handler)

    # init extensions
    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)

    with app.app_context():
        # TODO - register blueprints here. e.g.
        # from .routes import auth_blueprint
        # app.register_blueprint(auth_blueprint)


        # TODO register commands here e.g.
        from .commands import romwhist_cli
        app.cli.add_command(romwhist_cli)


        # finally create tables as per models
        db.create_all()


    return app
