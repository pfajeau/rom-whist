"""
This module implements routes.

author: Philippe Fajeau

"""
import threading
import traceback
from random import randint
from flask import render_template, request, flash, session, url_for, redirect
# from flask import Blueprint
from flask_login import current_user, login_user
from flask_socketio import emit
from flask_socketio import join_room, leave_room
import logging
import unidecode

from romwhist import common_routes
from romwhist import socketio
from romwhist.belote.belote import BeloteGame
from romwhist.extensions import db
from romwhist.forms import LoginForm, GameForm
from romwhist.belote.belote_form import BeloteStartForm
from romwhist.models import User
from romwhist import common_routes

NAMESPACE = '/belote'
NAMESPACE_AI = '/belote_ai'


# Map of games, key is game id
games = dict()

# Dictionary of session iDs for each game. This is a dictionary of Dictionary
# Keys are game ids and then player ids. Used for socketio.
clients = dict()


# @app.route("/belote_start",methods=['GET', 'POST'])
def belote_start():
    form = BeloteStartForm()
    if form.validate_on_submit():
        # Sanitize the username (as it isued as IDs in the html)
        username = common_routes.sanitize_username(form.user_name.data)
        logging.debug("User: " + username)

        # Used by client
        previous_alias = session.get('username')

        session['username'] = username
        if form.join_game.data:
            game_id = request.form['game_id']
            return common_routes.join_game(games, game_id, username, \
                                           'belote_start.html', 'belote_play', \
                                           NAMESPACE)

        elif form.start_game.data:
            logging.info("start game")
            game_id = common_routes.generate_game_id(999,games)
            if (game_id is None):
                return render_template('ohell_start.html', error="No more games available!!! Please try again later", form=form)

            points_to_reach = int(form.points_to_reach.data)

            logging.info("creating new game with id: " + str(game_id))
            # Add game id in session
            game = BeloteGame(game_creator=username, id=game_id)
            game.win_game_points = points_to_reach

            games[game_id] = game
            # players[game_id] = []
            clients[game_id] = dict()

            # dealing_method = request.form['dealing_method']
            # logging.info ("In route game, dealing method is: ", request.form['dealing_method'])
            dealing_method = "computer"
            session['ownername'] = username
            add_player(username, game_id)
            return redirect(url_for('belote_play'))
    else:
        return render_template("belote_start.html", form=form, error=form.errors)


# @app.route("/belote_play", methods=['GET', 'POST'])
def belote_play():
    logging.info("In belote_play route")
    form = GameForm()
    player = session.get('username')
    if player is None:
        flash("Session has expired")
        return redirect(url_for('belote_start'))

    game_id = session.get('game_id')
    if game_id is None:
        flash("Game does not exist")
        return redirect(url_for('belote_start'))

    game = games.get(game_id);
    if game is None:
        flash("Game does not exist")
        return redirect(url_for('belote_start'))

    if request.method == 'POST':
        # logging.info (request.form)
        if game_id is None:
            error = "Could not find game_id in session"
            logging.error(error)
            return render_template('belote_start.html', error=error)

        # if "stop_game" in request.form:
        if request.form['action_game'] == "stop_game":
            socketio.emit("game over", game.get_highest_score_player(), room=game_id, namespace=NAMESPACE)
            clean_game_data(game_id)
            return redirect(url_for('belote_start'))

        # if "leave_game" in request.form:
        if request.form['action_game'] == "leave_game":
            remove_player(game_id, session['username'])
            return redirect(url_for('belote_start'))

        if request.form['action_game'] == "remove_player":
            logging.info("Remve Player button pressed")
            rplayer = request.form['player_list']
            logging.info("Player to remove: " + rplayer)

            remove_player(game_id, rplayer)
            return redirect(url_for('belote_play'))

        if request.form['action_game'] == "restart_hand":
            restart_hand(game_id)
            return redirect(url_for('belote_play'))

        if request.form['action_game'] == "add_ai":
            common_routes.add_ai_player("ai_" + game_id + "_" + str(len(game.players)), \
                                        game_id, NAMESPACE_AI)
            return redirect(url_for('belote_play'))

    else:
        hand = game.get_hands().get(player)
        if hand is None:
            hand = []
        else:
            hand = hand.serialize()
        round = game.get_current_round()

        cards_played = game.get_cards_played()

        logging.debug("Active Player: " + game.get_active_player())
        logging.debug("Game Phase: " + game.phase.name)
        active_player = game.get_active_player()

        # logging.debug("Scoresheet:")
        # for i in range(game._current_hand_nb - 1):
        #     logging.debug(i, " ", game.scoresheet[i][0])
        #     logging.debug(i, " ", game.scoresheet[i][1])
        #     logging.debug(i, " ", game.scoresheet[i][2])

        # TODO Determine status of belote button
        # if game phase = play and user has both queen and king then enabled. If user has already play belote, then
        # enable.
        belote_enabled = False
        if game.belote_state == BeloteGame.BeloteState.Belote_Played or game.belote_state == BeloteGame.BeloteState.Allowed:
            belote_enabled = True

        return render_template("belote.html", form=form, players=game.get_playing_players(), scores=game.get_scores(), \
                               hand=hand, wins=game.hand_points, bets=game.get_bets(), active_player=active_player, \
                               cards_played=cards_played, allowed_cards=game.get_allowed_cards(active_player), \
                               trump=game.trump_card, trump_suit=game.trump_suit,
                               allowed_bets=game.allowed_bets(player), \
                               game_phase=game.phase.name, scoresheet=game.scoresheet, \
                               belote_allowed=belote_enabled, player_with_belote=game.player_with_belote)


# @app.route("/login",methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('belote_start'))
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
        return redirect(url_for("belote_start"))
    return render_template('login.html', title='Sign In', form=form)


# @app.route("/logout",methods=['GET', 'POST'])
# def logout():
#     remove_player()
#     logout_user()
#     return redirect(url_for('login'))

@socketio.on('message', namespace=NAMESPACE)
def message(data):
    logging.debug("message received");


@socketio.on("cs game started", namespace=NAMESPACE)
def game_started():
    game_id = session.get('game_id')
    if not game_id is None:
        game = games.get(game_id)
        if not game is None:
            # In automated dealing, call start_hands with computed nb of cards and trump
            # In case it is a restart
            game.reset()
            game.start_game()
            player = game.get_playing_players()[randint(0, len(game.get_playing_players()) - 1)]
            common_routes.emit_to_players(
                "sc game started",
                {'game_id': game_id, 'player_to_deal': player, 'deck_size': game.deck_size},
                room=game_id, namespace=NAMESPACE)

            generate_hands(game_id, player)


socketio.on("player bet", namespace=NAMESPACE_AI)
def player_bet_ai(data):
    logging.debug("player bet event received for ai")
    logging.debug("Player bet: " + str(data.get('bet')))
    player = data.get('player')
    game_id = data.get('game_id')
    bet = str(data.get('bet'))
    player_bet_process(player, game_id, bet)


@socketio.on("player bet", namespace=NAMESPACE)
def player_bet(bet):
    logging.info("player bet event received")
    logging.info("Player bet: " + bet)
    player = session['username']
    game_id = session.get('game_id')
    player_bet_process(player, game_id, bet)

def player_bet_process(player, game_id, bet):
    if game_id is None:
        logging.error("ERROR: Game not found!!!")
        return

    game = games.get(game_id)
    if game.phase == BeloteGame.GamePhase.BET or game.phase == BeloteGame.GamePhase.BET2:
        try:
            game.place_bet(player, bet)

            emit("player bet", {'player': username, 'bet': bet}, room=game_id, namespace=NAMESPACE)
            common_routes.emit_to_players(
                "player bet",
                {'game_id': game_id, 'player': player, 'bet': bet},
                room=game_id, namespace=NAMESPACE)

            nplayer = game.get_active_player()
            if game.phase == BeloteGame.GamePhase.DEAL:
                common_routes.restart_hand(game_id, NAMESPACE)

            elif game.phase == BeloteGame.GamePhase.BET or game.phase == BeloteGame.GamePhase.BET2:
                common_routes.emit_to_players(
                    "player to bet",
                    {'game_id': game_id, 'player': nplayer, 'allowed_bets': game.allowed_bets(nplayer)},
                    room=game_id, namespace=NAMESPACE)

            elif game.phase == BeloteGame.GamePhase.PLAY:
                hands = game.deal_2(game.dealer)
                logging.debug("After deal_2")
                round = game.create_round()
                # Distribute cards to each players
                for player in game.get_playing_players():
                    cards = hands[player].serialize()
                    logging.debug("Cards for player " + player + " " + str(cards))
                    socketio.emit("new hand", cards, room=clients[game_id][player], namespace=NAMESPACE)
                next_player_to_play = game.get_active_player()
                allowed_cards = game.get_hand(next_player_to_play).serialize()
                logging.debug("Allowed cards: " + str(allowed_cards))
                logging.debug("Player to play: " + next_player_to_play)

                emit("trump suit", game.trump_suit, room=game_id, namespace=NAMESPACE)
                common_routes.emit_to_players(
                    "trump suit",
                    game.trump_suit, game_id=game_id, room=game_id, namespace=NAMESPACE)

                common_routes.emit_to_players(
                    "player to play",
                    {'game_id': game_id, 'player': next_player_to_play, 'allowed_cards': allowed_cards},
                    room=game_id, namespace=NAMESPACE)

                player_belote = game.player_with_belote
                if (not player_belote is None):
                    logging.debug("Player with Belote / Rebelote: " + player_belote)
                    common_routes.emit_to_players(
                        "player to play",
                        player_belote, game_id=game_id,
                        room=clients[game_id][player_belote], namespace=NAMESPACE)
            return
        except Exception as e:
            logging.debug("Bet received: " + str(bet))
            logging.error(e)
            traceback.print_stack()
            emit("alert", "Error in place bet", room=clients[game_id][username], namespace=NAMESPACE)

# TODO: this could be factorized in common routes.
def hand_completed(game_id, username):
    game = games.get(game_id)
    if game is None:
        logging.error("Game with id %s does not exist", game_id)
        return

    # TODO: Is this call needed?
    game.hand_completed()
    scores = game.get_scores()
    logging.info("hand completed, next player to deal:" + game.next_player_to_deal())
    socketio.emit("hand completed", {'scores': scores, 'wins': game.hand_points,
                                     'hand_nb': game._current_hand_nb, 'player_to_deal': game.next_player_to_deal(),\
                                     'winners': game.hand_winner},
                room=game_id, namespace=NAMESPACE)

    if game.is_game_over():
        logging.debug("Game " + str(game_id) + " is over")
        common_routes.emit_to_players(
            "game over",
            game.get_highest_score_player(), game_id=game_id,
             room=game_id, namespace=NAMESPACE)
        logging.debug("Game " + str(game_id) + " is over")
        clean_game_data(game_id)

    else:
        generate_hands(game_id, "")


def next_round(game_id, nplayer, allowed_cards):
    game = games[game_id]
    game.create_round()

    socketio.emit("clear round", room=game_id, namespace=NAMESPACE)
    if game.is_hand_completed():
        hand_completed(game_id, nplayer)
    else:
        common_routes.emit_to_players(
            "player to play",
            {'game_id': game_id, 'player': nplayer, 'allowed_cards': allowed_cards},
            room=game_id, namespace=NAMESPACE)

@socketio.on('player played', namespace=NAMESPACE_AI)
def player_played_ai(data):
    logging.debug("player played event received for ai")
    logging.debug("Player card: " + data.get('card'))
    player = data.get('player')
    game_id = data.get('game_id')
    player_played_process(game_id, player, data.get('card'))

@socketio.on('player played', namespace=NAMESPACE)
def player_played(card):
    logging.info("card played event received")
    logging.info("Card played: " + card)
    game_id = session.get('game_id')
    player = session.get('username')
    player_played_process(game_id, player, card)


def player_played_process(game_id, player, card):
    # Emit event to players so they can see the card that was played
    if game_id is None:
        logging.error("Game id not specified")
        return

    common_routes.emit_to_players(
        "card played",
        {'game_id': game_id, 'player': player, 'card': card},
        room=game_id, namespace=NAMESPACE)

    game = games.get(game_id)
    belote_before = game.belote_state
    winner = game.card_played(session['username'], card)
    belote_after = game.belote_state

    if (belote_before != belote_after):
        belote_state_changed(game_id, session['username'])

    nplayer = game.get_active_player()

    if winner is None:
        # Round continues
        allowed_cards = game.get_allowed_cards(nplayer)
        common_routes.emit_to_players(
            "player to play",
             {'game_id': game_id, 'player': nplayer, 'allowed_cards': allowed_cards, "last_player": player},
             room=game_id, namespace=NAMESPACE)
    else:
        # There is a winnder, so round is ended
        # game.round_ended(winner)
        allowed_cards = game.get_hand(nplayer).serialize()
        winnning_card = game.get_current_round().cards_played[winner]
        common_routes.emit_to_players(
            "round ended",
            {"game_id": game_id, "winner": winner, "card": winnning_card.desc(), "last_player": player, "points":game.hand_points},
            room=game_id, namespace=NAMESPACE)

        timer = threading.Timer(6.0, next_round, [game_id, nplayer, allowed_cards])
        timer.start()

    logging.info("Allowed cards: " + str(allowed_cards))
    return


def belote_state_changed(game_id, player):
    logging.info("In belote played")
    game = games[game_id]
    belote_state = game.belote_state
    if belote_state == BeloteGame.BeloteState.Belote_Played:
        logging.info("Belote card played")
        socketio.emit("belote played", game.player_with_belote, room=game_id, namespace=NAMESPACE)

    elif belote_state == BeloteGame.BeloteState.Rebelote_Played:
        logging.info("Belote card played")
        socketio.emit("rebelote played", game.player_with_belote, room=game_id, namespace=NAMESPACE)

    elif belote_state == BeloteGame.BeloteState.Lost:
        logging.info("Belote points lost")
        socketio.emit("belote lost", game.player_with_belote, room=game_id, namespace=NAMESPACE)

    return


# TODO factorize with ohell
def generate_hands(game_id, username, nbcards=5, trump=True):
    game = games.get(game_id)
    if game is None:
        logging.error("Unknown game: " + str(game_id))
        return

    hands = game.deal_1(username)

    # FInd out who the first player to bet is
    nplayer = game.get_active_player()

    # Distribute cards to each players
    for player in game.get_playing_players():
        cards = hands[player].serialize()
        logging.info("Cards for player " + player + " " + str(cards))
        common_routes.emit_to_players(
            "new hand",
            {'game_id': game_id, 'player': player, 'cards': cards},
            room=clients[game_id].get(player), namespace=NAMESPACE)

    common_routes.emit_to_players(
        "trump card",
        {"game_id": game_id, "trump_card": str(game.trump_card), "trump_suit": str(game.trump_suit)},
        room=game_id, namespace=NAMESPACE)

    common_routes.emit_to_players(
        "player to bet",
        {'game_id': game_id, 'player': nplayer, 'allowed_bets': game.allowed_bets(player)},
        room=game_id, namespace=NAMESPACE)
    return


@socketio.on('belote announced', namespace=NAMESPACE)
def belote_announced(announce):
    logging.info("belote announced event received. Announce is: " + announce)
    # Set in game and issue notification if applicable
    game_id = session.get('game_id')
    if not game_id is None:
        player = session.get('username')
        game = games[game_id]
        if announce == 'Belote':
            game.player_announced_belote(player, BeloteGame.BeloteAnnounced.BELOTE)
        elif announce == 'Rebelote':
            game.player_announced_belote(player, BeloteGame.BeloteAnnounced.REBELOTE)

        # emit("alert", announce + " announced by " + player, room=game_id, namespace=NAMESPACE)
        common_routes.emit_to_players(
            "belote announced",
            {'game_id': game_id, 'player': player, 'announced': announce},
            room=game_id, namespace=NAMESPACE)
        emit("msg posted", {'sender': session['username'], 'msg': announce}, room=game_id, namespace=NAMESPACE)


@socketio.on('join game', namespace=NAMESPACE)
def on_join(data):
    # Note that a refresh on the client side causes the socketio sid to changed
    # so need to remove the previous sid from the room
    logging.info("on_join")
    game_id = session.get('game_id')
    if not game_id is None:
        if session['game_id'] in games:
            # Add user to room if user is not there already
            player = session.get('username')
            current_client_room = clients[game_id].get(player)

            # Adding new client room id (sid) to list of clients
            clients[game_id][player] = request.sid
            session['sid'] = request.sid
            join_room(game_id)

# TODO: factorize
@socketio.on('join game ai', namespace=NAMESPACE_AI)
def join_ai(data):
    # Note that a refresh on the client side causes the socketio sid to changed
    # so need to remove the previous sid from the room
    logging.info("join_ai")

    game_id = str(data.get('game_id'))
    game = games.get(game_id)
    if game is None:
        logging.error("Unknown game: " + repr(game_id))
        return
    # Add user to room if user is not there already
    player = data.get('player')
    logging.debug("Player: " + player)
    common_routes.add_player(player, game, NAMESPACE)

@socketio.on('client post', namespace=NAMESPACE)
def on_post(msg):
    # Just distribute to players in room
    common_routes.post_msg(msg, session['username'], session.get('game_id'), NAMESPACE)


@socketio.on('disconnect', namespace=NAMESPACE)
def test_disconnect():
    player = session.get('username')
    game_id = session.get('game_id')
    logging.info('Client disconnected. ' + str(player))
    client_id = request.sid
    if not game_id is None:
        leave_room(game_id)
        timer = threading.Timer(120.0, check_player_left, [player, game_id, client_id])
        timer.start()


def check_player_left(player, game_id, client_id):
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

def restart_hand(game_id):
    game = games.get(game_id)
    if game is None:
        return
    socketio.emit("alert", "Hand to be replayed", room=game_id, namespace=namespace)
    if game.started:
        # Deal another hand
        game._current_hand_nb = game._current_hand_nb - 1
        generate_hands(game.id, game.dealer)


# Add player to a game
def add_player(player, game_id):
    game = games.get(game_id)
    if not game is None:
        common_routes.add_player(player, game, NAMESPACE)
        if game.started:
            restart_hand(game_id)

# TODO: factorize
def remove_player(game_id, player):
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

        socketio.emit("player left", player, room=game_id, namespace=NAMESPACE)
        socketio.emit("clear round", room=game_id, namespace=NAMESPACE)
        restart_hand(game_id)


def clean_game_data(game_id):
    game = games.get(game_id)
    if game is None:
        return
    del games[game_id]
    del clients[game_id]
# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
