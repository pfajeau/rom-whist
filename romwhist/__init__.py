"""
App init module

@author: Philippe Fajeau
"""
"""
App init module

@author: Philippe Fajeau
"""

from flask import Flask
from flask_login import LoginManager
import logging
import logging.handlers
from .extensions import *
from flask_bootstrap import Bootstrap
from flask_socketio import SocketIO

app = Flask(__name__, instance_relative_config=True, template_folder="ui/templates", static_folder="ui/static")
socketio = SocketIO(app, logger=True)

#app = Flask(__name__, instance_relative_config=True, template_folder="ui/templates", static_folder="ui/static")
#socketio = SocketIO(app)

#from .routes import *
from ohell import ohell_routes

app.add_url_rule('/', view_func=ohell_routes.index, methods=["GET", "POST"])
app.add_url_rule('/index', view_func=ohell_routes.index, methods=["GET", "POST"])
app.add_url_rule('/ohell_play', view_func=ohell_routes.ohell_play, methods=["GET", "POST"])

# When adding those, events are not received by the client anymre
# app.add_url_rule('/belote_start', view_func=belote_routes.belote_start, methods=["GET", "POST"])
# app.add_url_rule('/belote_play', view_func=belote_routes.belote_play, methods=["GET", "POST"])

def create_app():
    login_manager = LoginManager()
    Bootstrap(app)
    app.config.from_pyfile("config.py")

    # logging
    handler = logging.handlers.RotatingFileHandler(app.config["LOG_FILE"], maxBytes=app.config["LOG_SIZE"])
    handler.setLevel(app.config["LOG_LEVEL"])
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(levelname)s [%(pathname)s at %(lineno)s]: %(message)s", "%Y-%m-%d %H:%M:%S"))
    # app.logger.addHandler(handler)

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
