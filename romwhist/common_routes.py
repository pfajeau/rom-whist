"""
This module implements common code betwenn routes.

author: Philippe Fajeau

"""
import logging
from random import randint

import unidecode
from flask import render_template, session, url_for, flash, redirect, request
# from flask import Blueprint
from flask_babel import gettext as _

from flask_login import current_user, login_user
from romwhist import socketio
from romwhist.belote import belote_routes
from romwhist.extensions import db
from romwhist.forms import LoginForm
from romwhist.models import User
from romwhist.ohell import ohell_routes
from romwhist import app
from romwhist import i18n_strings


def get_locale(request):
    print(app.config['LANGUAGES'])
    return request.accept_languages.best_match(app.config['LANGUAGES'])

# TODO: separate from this file to remove circular dependency between
#  game specific routes modules and this module
def admin():
    return render_template('admin.html', nb_belote_games = len(belote_routes.games),
                           nb_whist_games =len(ohell_routes.games))


def home():
    locale = get_locale(request)
    return render_template("home.html", locale=locale)


#@app.route("/base")
def base():
    return render_template("base.html")


# @app.route("/login",methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        logging.debug("User name from form:" + form.username.data)
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            user = User(username=form.username.data)
            db.session.add(user)
            db.session.commit()
        login_user(user, remember=form.remember_me.data)
        logging.debug ("current user: " + session['username'])
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


def redirect_game_start(games, action, template_to_render, namespace):
    player = session.get('username')
    if player is None:
        logging.error("Unknown player in session")
        flash(_('session_has_expired'))
        return redirect(url_for(template_to_render))

    game_id = session.get('game_id')
    if game_id is None:
        logging.error("Unknown game id: %s", game_id)
        flash(_("game_does_not_exist"))
        return redirect(url_for(template_to_render))

    game = games.get(game_id)
    if game is None:
        logging.error("Unknown game: %s", game_id)
        flash(_("game_does_not_exist"))
        return redirect(url_for(template_to_render))

    if request.method == 'POST':
        # logging.info (request.form)

        # if "stop_game" in request.form:
        if action == "stop_game":
            socketio.emit(_("game_over"), game.get_highest_score_player(), room=game_id, namespace=namespace)
            clean_game_data(game_id)
            return redirect(url_for(template_to_render))

        # if "leave_game" in request.form:
        if request.form['action_game'] == "leave_game":
            remove_player(game_id, session['username'])
            return redirect(url_for(template_to_render))

    return None


def remove_player(game_id, games, clients, player, namespace):
    # game_id = session.get('game_id')
    if not game_id is None:
        game = games.get(game_id)
        if not game is None:
            if game.started:
                game.disable_player(player)
            else:
                game.remove_player(player)
                if player in clients[game_id]:
                    del clients[game_id][player]

        socketio.emit("player left", player, room=game_id, namespace=namespace)
        socketio.emit("clear round", room=game_id, namespace=namespace)
    return


def clean_game_data(game_id, games, clients):
    game = games.get(game_id)
    if game is None:
        return
    del games[game_id]
    del clients[game_id]


def post_msg(msg, sender, room, namespace):
    game_id = session.get('game_id')
    if game_id is None:
        logging.warning("NO GAME_ID IN SESSION!!!!")
    else:
        socketio.emit("msg posted", {'sender': sender, 'msg': msg}, room=room, namespace=namespace)

# def restart_hand(game, namespace):
#     # Deal another hand
#     socketio.emit("alert", "Hand to be replayed", room=game.id, namespace=namespace)
#     if game.started:
#       game._current_hand_nb = game._current_hand_nb - 1  # Deal again
#       generate_hands(game.id, game.dealer)


def add_player(user, game, namespace):
    game.add_player(user)
    socketio.emit("new player", user, room=game.id, namespace=namespace)


# To create an ai player
def add_ai_player(nb_players, game_id, namespace):
    ai_name = "ai" + game_id + "_" + str(nb_players)
    socketio.emit("create_ai_player", {"name": ai_name, "game_id": game_id}, namespace=namespace)


def sanitize_username(username1):
    # Sanitize the username (as it isued as IDs in the html)
    username = unidecode.unidecode(username1)
    username = username.replace(" ", "")
    return username


def join_game(games, game_id, username, start_page, play_page, namespace, form, max_players=6):
    logging.debug("game id: " + game_id)
    if not game_id in games:
        error = _("game_not_created")
        logging.error(error)
        return render_template(start_page, error=error, form=form)

    game = games[game_id]
    # Not allowed to connect if another player has the same alias
    # and game has not started. If game has started, assume player
    # is trying to reconnect after having lost a connection
    if username in game.get_players() and not game.started:
        error = _("game_has_user_with_same_name")
        logging.info(error)
        return render_template(start_page, error=error, form=form)

    # Not allowed to connect to a game already started unless the player
    # is already an existing player (same alias)
    if game.started and not username in game.get_players():
        error = _("game_already_started")
        logging.info(error)
        return render_template(start_page, error=error, form=form)

    # Remove player from game if that player was already in the games
    # if previous_alias in players[game_id]:
    #     remove_player(game_id, previous_alias)

    if len(game.get_playing_players()) >= max_players:
        flash(_("game_already_has_4_players"))
        return render_template('contree_start.html',
                               error=_("game_already_has_max_players"),
                               form=form, locale=get_locale(request))

    session['ownername'] = game.owner
    add_player(username, game, namespace)
    return redirect(url_for(play_page))


def generate_game_id(max_id, games):
    if len(games) == max_id:
        error = "No more games available!!! Please try again later"
        logging.error(error)
        return None

    game_id = str(randint(1, max_id))
    while game_id in games:
        game_id = str(randint(1, max_id))
    logging.debug("game_id:" + str(game_id))
    return game_id


def next_round(game, nplayer, allowed_cards, hand_completed_cb, namespace):
    game.create_round()
    game_id = game.id

    socketio.emit("clear round", room=game.id, namespace=namespace)
    if game.is_hand_completed():
        hand_completed_cb(game_id, nplayer)
    else:
        emit_to_players(
            "player to play",
            {'game_id': game_id, 'player': nplayer, 'allowed_cards': allowed_cards},
            room=game_id, namespace=namespace, game_state=game.get_state())


# Utility mothod to emit an event to both real players and the ai players
# data must contain the game_id
def emit_to_players(event, data, game_id=None, room=None, namespace=None, game_state=None):
    if room is not None:
        # If room specified assumes it goes to the web clients
        socketio.emit(event, data, game_id = game_id, room=room, namespace=namespace)

    if game_id is None:
        # In this case, the game_id has to be part of the data being passed
        game_id = data.get("game_id")
        if game_id is None:
            logging.error("game_id not specified")
        else:
            if game_state is not None:
                data['state'] = game_state.toJson()
            socketio.emit(event, data, namespace=namespace + "_ai")
        return

    else:
        # game_id is passed to this function
        # Add game_id to the parameters for the event
        # TODO refactor so that all calls include the game id in the
        # data being passed
        data2 = dict()
        if isinstance(data, dict):
            data2 = data
            data2["game_id"] = game_id
            if game_state is not None:
                data2['state'] = game_state.toJson()
        else:
            data2["game_id"] = game_id
            data2['param'] = data
            if game_state is not None:
                data2['state'] = game_state.toJson()

        socketio.emit(event, data2, namespace=namespace+"_ai")



