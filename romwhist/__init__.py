"""
App init module

@author: Philippe Fajeau
"""
"""
App init module

@author: Philippe Fajeau
"""

from flask import Flask
from flask import request
from flask_login import LoginManager
from flask_babel import Babel

import logging
import logging.handlers
from .extensions import *
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO

app = Flask(__name__, instance_relative_config=True, template_folder="ui/templates", static_folder="ui/static")
socketio = SocketIO(app, logger=True)

# app = Flask(__name__, instance_relative_config=True, template_folder="ui/templates", static_folder="ui/static")
# socketio = SocketIO(app)

from .ohell import ohell_routes

app.add_url_rule('/ohell_start', view_func=ohell_routes.ohell_start, methods=["GET", "POST"])
app.add_url_rule('/ohell_play', view_func=ohell_routes.ohell_play, methods=["GET", "POST"])

from .belote import belote_routes

app.add_url_rule('/belote_start', view_func=belote_routes.belote_start, methods=["GET", "POST"])
app.add_url_rule('/belote_play', view_func=belote_routes.belote_play, methods=["GET", "POST"])

from .contree import contree_routes

app.add_url_rule('/contree_start', view_func=contree_routes.contree_start, methods=["GET", "POST"])
app.add_url_rule('/contree_play', view_func=contree_routes.contree_play, methods=["GET", "POST"])

from romwhist import common_routes

app.add_url_rule('/', view_func=common_routes.home, methods=["GET", "POST"])
app.add_url_rule('/admin', view_func=common_routes.admin, methods=["GET", "POST"])
app.add_url_rule('/home', view_func=common_routes.home, methods=["GET", "POST"])

babel = Babel(app)


def create_app():
    login_manager = LoginManager()
    Bootstrap(app)
    app.config.from_pyfile("config.py")

    # logging
    # handler = logging.handlers.RotatingFileHandler(app.config["LOG_FILE"], maxBytes=app.config["LOG_SIZE"])
    handler = logging.FileHandler(app.config["LOG_FILE"])
    print("Log file: " + app.config["LOG_FILE"])
    handler.setLevel(app.config["LOG_LEVEL"])
    handler.setFormatter(
        logging.Formatter("[%(asctime)s] %(levelname)s [%(pathname)s at %(lineno)s]: %(message)s", "%Y-%m-%d %H:%M:%S"))
    app.logger.addHandler(handler)
    logging.basicConfig(filename=app.config["LOG_FILE"],
                        format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s",
                        level=app.config["LOG_LEVEL"])

    # Initialize Flask-Babel
    # babel = Babel(app)

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


# Use the browser's language preferences to select an available translation
# add to you main app code
@babel.localeselector
def get_locale():
    print(app.config['LANGUAGES'])
    return request.accept_languages.best_match(app.config['LANGUAGES'])
