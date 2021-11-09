"""
This module implements common code between routes.

author: Philippe Fajeau
"""

import logging
from random import randint
import threading

import unidecode
from flask import render_template, session, url_for, flash, redirect, request
# from flask import Blueprint
from flask_babel import gettext as _
from flask_socketio import join_room, leave_room

from flask_login import current_user, login_user
from romwhist import socketio
from romwhist.belote import belote_routes
from romwhist.belote.belote_status import BeloteStatus
from romwhist.card import Card
from romwhist.contree import contree_routes
from romwhist.extensions import db
from romwhist.forms import LoginForm
from romwhist.models import User
from romwhist.ohell import ohell_routes
from romwhist.player import Player
from romwhist.belote.belote import BeloteGame
from romwhist import app


def get_locale(the_request):
    print(app.config['LANGUAGES'])
    return the_request.accept_languages.best_match(app.config['LANGUAGES'])


# TODO: separate from this file to remove circular dependency between
#  game specific routes modules and this module
def admin():
    return render_template('admin.html',
                           nb_belote_games=len(belote_routes.games),
                           nb_whist_games=len(ohell_routes.games),
                           nb_contree_games=len(contree_routes.games))


def home():
    locale = get_locale(request)
    return render_template("home.html", locale=locale)


# @app.route("/base")
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
        logging.debug("current user: " + session['username'])
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)


def redirect_game_start(games, clients, action, template_to_render, namespace):
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
            clean_game_data(game_id, games, clients)
            return redirect(url_for(template_to_render))

        # if "leave_game" in request.form:
        if request.form['action_game'] == "leave_game":
            remove_player(game_id, games, clients, session['username'], namespace=namespace)
            return redirect(url_for(template_to_render))

    return None


def remove_player(game_id, games, clients, player, namespace):
    # game_id = session.get('game_id')
    if game_id is not None:
        socketio.emit("player left", player, room=game_id,
                      skip_sid=clients[game_id][player], namespace=namespace)

        game = games.get(game_id)
        if game is not None:
            if game.started:
                game.disable_player(player)
            else:
                game.remove_player(player)
                if player in clients[game_id]:
                    del clients[game_id][player]

        socketio.emit("clear round", room=game_id, namespace=namespace)
    return


def clean_game_data(game_id, games, clients):
    game = games.get(game_id)
    if game is None:
        return
    del games[game_id]
    del clients[game_id]


def post_msg(msg, sender, room, messages, namespace):
    game_id = session.get('game_id')
    if game_id is None:
        logging.warning("NO GAME_ID IN SESSION!!!!")
    else:
        socketio.emit("msg posted", {'sender': sender, 'msg': msg}, room=room, namespace=namespace)
        message_key = game_id
        if message_key not in messages:
            messages[message_key] = []
        messages[message_key].append(sender + ": " + msg)

# def restart_hand(game, namespace):
#     # Deal another hand
#     socketio.emit("alert", "Hand to be replayed", room=game.id, namespace=namespace)
#     if game.started:
#       game._current_hand_nb = game._current_hand_nb - 1  # Deal again
#       generate_hands(game.id, game.dealer)


def add_player_by_name(player_name, game, namespace):
    new_player = Player(player_name)
    add_player(new_player, game, namespace)


def add_player(player, game, namespace):
    game.add_player(player)
    socketio.emit("new player", player.name, room=game.id, namespace=namespace)


# To create an ai player
def add_ai_player(nb_players, game_id, namespace):
    ai_name = "ai" + game_id + "_" + str(nb_players)
    socketio.emit("create_ai_player", {"name": ai_name, "game_id": game_id}, namespace=namespace)


def sanitize_username(username1):
    # Sanitize the username (as it used as IDs in the html)
    username = unidecode.unidecode(username1)
    username = username.replace(" ", "")
    return username


def join_game(games, game_id, username, start_page, play_page, namespace, form, max_players=6):
    logging.debug("game id: " + game_id)
    if game_id not in games:
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
    if game.started and username not in game.get_players():
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


def belote_status_changed(game_id, game, namespace):
    logging.info("In belote_status_changed")
    belote_status = game.belote_status
    if belote_status == BeloteStatus.Belote_Played:
        logging.info("Belote card played")
        socketio.emit("belote played", game.player_with_belote, room=game_id, namespace=namespace)

    elif belote_status == BeloteStatus.Rebelote_Played:
        logging.info("Belote card played")
        socketio.emit("rebelote played", game.player_with_belote, room=game_id, namespace=namespace)

    elif belote_status == BeloteStatus.Lost:
        logging.info("Belote points lost")
        socketio.emit("belote lost", game.player_with_belote, room=game_id, namespace=namespace)
    return


def belote_announced(announce, games, namespace):
    logging.info("belote announced event received. Announce is: " + announce)
    # Set in game and issue notification if applicable
    game_id = session.get('game_id')
    if game_id is not None:
        player = session.get('username')
        game = games[game_id]

        belote_announced2(announce, game, player, namespace)
    return


def belote_announced2(announce, game, player, namespace):
    if announce == 'belote':
        game.player_announced_belote(player, BeloteGame.BeloteAnnounced.BELOTE)
    elif announce == 'rebelote':
        game.player_announced_belote(player, BeloteGame.BeloteAnnounced.REBELOTE)

    # emit("alert", announce + " announced by " + player, room=game_id, namespace=NAMESPACE)
    emit_to_players(
        "belote announced",
        {'game_id': game.id, 'player': player, 'announced': announce},
        room=game.id, namespace=namespace)
    socketio.emit("msg posted", {'sender': session['username'], 'msg': announce}, room=game_id, namespace=namespace)
    return


def belote_rebelote_ai(game, card_played, player, namespace):
    queen_t = Card.get_suit_initial(game.trump_suit) + "12"
    king_t = Card.get_suit_initial(game.trump_suit) + "13"

    belote_ok = game.player_with_belote == player and \
                game.has_player_card(player, queen_t) and \
                game.has_player_card(player,king_t) and \
                (card_played == queen_t or card_played == king_t)
    if belote_ok:
        belote_announced2(BeloteGame.BeloteAnnounced.BELOTE, game, player, namespace)

    else:
        rebelote_ok = game.player_with_belote == player and \
                      game.belolote_status == BeloteStatus.Belote_Played and \
                      (card_played == queen_t or card_played == king_t)
        if rebelote_ok:
            belote_announced2(BeloteGame.BeloteAnnounced.REBELOTE, game, player, namespace)


def on_join(game_id, games, clients, namespace):
    # Note that a refresh on the client side causes the socketio sid to changed
    # so need to remove the previous sid from the room
    logging.info("on_join")
    if game_id is not None:
        if session['game_id'] in games:
            # Add user to room if user is not there already
            player_name = session.get('username')
            logging.debug("Player: " + player_name)

            # Adding new client room id (sid) to list of clients
            clients[game_id][player_name] = request.sid
            session['sid'] = request.sid
            join_room(game_id, namespace=namespace)
    return


def join_ai(game_id, player_name, games, namespace):
    # Note that a refresh on the client side causes the socketio sid to changed
    # so need to remove the previous sid from the room
    logging.info("join_ai with player %s", player_name)

    game = games.get(game_id)
    if game is None:
        logging.error("Unknown game: " + repr(game_id))
        return
    # Add user to room if user is not there already
    player = Player(player_name)
    player.player_type = Player.PlayerType.AI
    add_player(player, game, namespace)
    return


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


# Utility method to emit an event to both real players and the ai players
# data must contain the game_id
def emit_to_players(event, data, game_id=None, room=None, namespace=None, game_state=None):
    if room is not None:
        # If room specified assumes it goes to the web clients
        socketio.emit(event, data, game_id=game_id, room=room, namespace=namespace)

    if game_id is None:
        # In this case, the game_id has to be part of the data being passed
        game_id = data.get("game_id")
        if game_id is None:
            logging.error("game_id not specified")
        else:
            if game_state is not None:
                data['state'] = game_state.to_json()
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
                data2['state'] = game_state.to_json()
        else:
            data2["game_id"] = game_id
            data2['param'] = data
            if game_state is not None:
                data2['state'] = game_state.to_json()

        socketio.emit(event, data2, namespace=namespace+"_ai")


def disconnect(clients):
    player = session.get('username')
    game_id = session.get('game_id')
    logging.info('Client disconnected. ' + str(player))
    client_id = request.sid
    if game_id is not None:
        leave_room(game_id)
        timer = threading.Timer(120.0, check_player_left, [player, game_id, client_id, clients])
        timer.start()


def check_player_left(player, game_id, client_id, clients):
    # If the player still exist with a client_id that has not changed
    # it means that the player has closed the browser window or
    # something similar. In this case, the player has to be removed
    # from the game. If the client_id has changed, it just mean
    # a refresh page has happened, so leave the player in the game

    # Do nothing, let game owner remove user manually if needed
    players = clients.get(game_id)
    if players is None:
        return

    # if player in players:
    #     current_client_id = clients[game_id][player]
    #     if current_client_id == client_id:
    # remove_player(game_id, player)
