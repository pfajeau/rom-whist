"""
This module implements common code betwenn routes.

author: Philippe Fajeau

"""
from random import randint
import unidecode
import threading
import traceback
from flask import render_template, request, flash, session, url_for, redirect
#from flask import Blueprint
from flask_login import current_user, login_user, logout_user, AnonymousUserMixin
from flask_socketio import join_room, leave_room
from flask_socketio import SocketIO, emit
import logging

from romwhist import controllers,deck,card,hand
from romwhist import socketio,app
from romwhist.forms import LoginForm
from romwhist.models import User
from romwhist.extensions import db
from romwhist.ohell import ohell_routes
from romwhist.belote import belote_routes

# TODO: separate from this file to remove circular dependency between
#  game specific routes modules and this module
def admin():
    return render_template('admin.html', nb_belote_games = len(belote_routes.games), \
                           nb_whist_games =len(ohell_routes.games))

def home():
    return render_template("home.html")


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
def add_ai_player(player_name, game_id, namespace):
    socketio.emit("create_ai_player", {"name": player_name, "game_id": game_id}, namespace=namespace)


def sanitize_username(username1):
    # Sanitize the username (as it isued as IDs in the html)
    username = unidecode.unidecode(username1)
    username = username.replace(" ", "")
    return username


def join_game(games, game_id, username, start_page, play_page, namespace):
    logging.debug("game id: " + game_id)
    if not game_id in games:
        error = "This game has not been created yet"
        logging.error(error)
        return render_template(start_page, error=error, form=form)

    game = games[game_id]
    # Not allowed to connect if another player has the same alias
    # and game has not started. If game has started, assume player
    # is trying to reconnect after having lost a connection
    if username in game.get_players() and not game.started:
        error = "The game already has a user with the same name"
        logging.info(error)
        return render_template(start_page, error=error, form=form)

    # Not allowed to connect to a game already started unless the player
    # is already an existing player (same alias)
    if game.started and not username in game.get_players():
        error = "This game has already started! You cannot join a game in progress"
        logging.info(error)
        return render_template(start_page, error=error, form=form)

    # Remove player from game if that player was already in the games
    # if previous_alias in players[game_id]:
    #     remove_player(game_id, previous_alias)

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

# Utility mothod to emit an event to both real players and the ai players
# data must contain the game_id
def emit_to_players(event, data, game_id=None, room=None, namespace=None):
    # If no room speified assumes it is not for any web clients
    if room is not None:
        socketio.emit(event, data, game_id = None, room=room, namespace=namespace)

    if game_id is None:
        # In this case, teh game_id has to be part of the data being passed
        game_id = data.get("game_id")
        if game_id is None:
            logging.error("game_id not specified")
            return
        else:
            socketio.emit(event, data, namespace=namespace + "_ai")
            return

    else:
        # game_id is passed to this function
        data2 = dict()
        # Add game_id to the parameters for the event
        # TODO refactor so that all calls include the game id in the
        # data being passed
        if isinstance(data, dict):
            data2 = data
            data2["game_id"] = game_id
        else:
            data2["game_id"] = game_id
            data2['param'] = data

        socketio.emit(event, data2, namespace=namespace+"_ai")


def emit_game_state(game_id, player, game_state, namespace):
    socketio.emit('game_state',
                  {'game_id': game_id, 'player': player, 'state': game_state},
                  namespace=namespace)
