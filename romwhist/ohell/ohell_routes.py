"""
This module implements routes.

author: Philippe Fajeau

"""
import threading
import traceback
from random import randint

import unidecode
from flask import render_template, request, flash, session, url_for, redirect
# from flask import Blueprint
from flask_login import current_user, login_user
from flask_socketio import emit
from flask_socketio import join_room, leave_room
import logging

from romwhist import socketio, app
from romwhist.extensions import db
from romwhist.forms import LoginForm, GameForm
from romwhist.ohell.ohell_form import OhellStartForm
from romwhist.models import User
from romwhist.ohell.ohell import OhellGame
from romwhist import common_routes

from subprocess import Popen, PIPE

NAMESPACE = '/ohell'

# Map of games, key is game id
games = dict()

# Dictionary of session iDs for each game. This is a dictionary of Dictionary
# Keys are game ids and then player ids. Used for socketio.
clients = dict()


# TODO: move this route to a common route file
def home():
    return render_template("home.html")


def ohell_start():
    # logging.debug (current_user)
    # if isinstance(current_user, User):
    #     logout_user()
    #     #user = User(username=user_name)
    #     db.session.delete(current_user)
    #     db.session.commit()
    #
    # user = User.query.filter_by(username=user_name).first()
    # logging.debug ("User retrieved:" + user)
    # if user is None:
    # user = User(username=user_name)
    # db.session.add(user)
    # db.session.commit()
    # login_user(user)
    form = OhellStartForm()
    if form.validate_on_submit():
        # Sanitize the username (as it isued as IDs in the html)
        # username = unidecode.unidecode(form.user_name.data)
        # username = username.replace(" ", "")
        username = common_routes.sanitize_username(form.user_name.data)
        logging.debug("User: " + username)

        # Used by client
        previous_alias = session.get('username')

        session['username'] = username
        if form.join_game.data:
            game_id = request.form['game_id']
            return common_routes.join_game(games, game_id, username, \
                                           'ohell_start.html', 'ohell_play', \
                                           NAMESPACE)

        elif form.start_game.data:
            logging.info("start game")
            game_id = common_routes.generate_game_id(999,games)
            if (game_id is None):
                return render_template('ohell_start.html', error="No more games available!!! Please try again later", form=form)

            logging.debug("creating new game with id: " +str(game_id))
            # Add game id in session
            game = OhellGame(game_creator=username, deck_size=0, id=game_id)
            games[game_id] = game
            # players[game_id] = []
            clients[game_id] = dict()

            # dealing_method = request.form['dealing_method']
            dealing_method = "computer"
            if dealing_method == "computer":
                multiple_one_card = 'multiple_one_card' in request.form.keys()
                multiple_no_trump = 'multiple_no_trump' in request.form.keys()
                game.set_hand_prgression(
                    multiple_one_card, multiple_no_trump,
                    int(request.form['increment']))

            session['ownername'] = username
            add_player(username, game_id)
            return redirect(url_for('ohell_play'))
    else:
        return render_template("ohell_start.html", form=form, error=form.errors)


@app.route("/base")
def base():
    return render_template("base.html")


def ohell_play():
    logging.debug("In ohell_play route")
    form = GameForm()
    player = session.get('username')
    logging.debug("Player name: " + player)
    if player is None:
        flash("Session has expired")
        return redirect(url_for('ohell_start'))

    game_id = session.get('game_id')
    if game_id is None:
        flash("Game does not exist")
        return redirect(url_for('ohell_start'))

    game = games.get(game_id);
    if game is None:
        flash("Game does not exist")
        return redirect(url_for('ohell_start'))

    if request.method == 'POST':
        # logging.debug (request.form)
        if game_id is None:
            error = "Could not find game_id in session"
            logging.debug(error)
            return render_template('ohell_start.html', error=error)

        # if "stop_game" in request.form:
        if request.form['action_game'] == "stop_game":
            socketio.emit("game over", game.get_highest_score_player(), room=game_id, namespace=NAMESPACE)
            clean_game_data(game_id)
            return redirect(url_for('ohell_start'))

        # if "leave_game" in request.form:
        if request.form['action_game'] == "leave_game":
            remove_player(game_id, session['username'])
            return redirect(url_for('ohell_start'))

        if request.form['action_game'] == "remove_player":
            logging.info("Remove Player button pressed")
            rplayer = request.form['player_list']
            logging.info("Player to remove: " + rplayer)

            remove_player(game_id, rplayer)
            return redirect(url_for('ohell_play'))

        if request.form['action_game'] == "restart_hand":
            restart_hand(game_id)

    else:
        hand = game.get_hands().get(player)
        if hand is None:
            hand = []
        else:
            hand = hand.serialize()
        round = game.get_current_round()

        cards_played = game.get_cards_played()

        logging.debug("Player: "+ player)
        logging.debug("Active Player: " + game.get_active_player())
        logging.debug("Game Phase: " + game.phase.name)
        active_player = game.get_active_player()
        logging.debug ("Allowed cards: " + str(game.get_allowed_cards(player)))
        # logging.debug("Scoresheet:")
        # for i in range(game._current_hand_nb - 1):
        #     logging.debug(i, " ", game.scoresheet[i][0])
        #     logging.debug(i, " ", game.scoresheet[i][1])
        #     logging.debug(i, " ", game.scoresheet[i][2])

        return render_template("ohell.html", form=form, players=game.get_playing_players(), scores=game.get_scores(), \
                               hand=hand, bets=game.get_bets(), wins=game.get_wins(), active_player=active_player, \
                               cards_played=cards_played, allowed_cards=game.get_allowed_cards(player), \
                               trump=game.trump_card, dealing_method=game.dealing_method, \
                               allowed_bets=game.allowed_bets(player), game_phase=game.phase.name, \
                               hand_nb=game._nb_cards_per_hand, scoresheet=game.scoresheet)


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


# @app.route("/logout",methods=['GET', 'POST'])
# def logout():
#     remove_player()
#     logout_user()
#     return redirect(url_for('login'))

@socketio.on('message', namespace=NAMESPACE)
def message(data):
    logging.info("message received");


@socketio.on("cs game started", namespace=NAMESPACE)
def game_started():
    game_id = session.get('game_id')
    if not game_id is None:
        game = games.get(game_id)
        if not game is None:
            # If manual dealiing, just emit event game sc game started
            # In automated dealing, call start_hands with computed nb of cards and trump
            # In case it is a restart
            game.reset()
            game.start_game()
            player = game.get_playing_players()[randint(0, len(game.get_playing_players()) - 1)]
            socketio.emit("sc game started", {'player_to_deal': player, 'nb_cards': 0}, room=game_id,
                          namespace=NAMESPACE)

            logging.debug("Dealing method is: " + games[game_id].dealing_method)
            if games[game_id].dealing_method == OhellGame.AUTOMATED_DEALING:
                generate_hands(game_id, player)

            # Test AI
            # process = Popen(['python -m ', 'romwhist.ai_player'], stdout=PIPE, stderr=PIPE)
            # add_player("AI1", game_id)


@socketio.on("player bet", namespace=NAMESPACE)
def player_bet(bet):
    logging.info("player bet event received")
    logging.info("Player bet: " + bet)
    username = session.get('username')
    game_id = session.get('game_id')
    if game_id is None:
        logging.error("ERROR: Game not found!!!")
    else:
        game = games[game_id]
        try:
            bet_int = int(bet)
            game.place_bet(session.get('username'), bet_int)
            emit("player bet", {'player': session.get('username'), 'bet': bet}, room=game_id, namespace=NAMESPACE)
            nplayer = game.next_player_to_bet(username)

            if nplayer is None:
                # All players have bet
                next_player_to_play = game.get_active_player()
                # All cards allowed for first player
                allowed_cards = game.get_hand(next_player_to_play).serialize()
                logging.debug("Allowed cards: " + str(allowed_cards))
                logging.debug("Player to play: " + next_player_to_play)
                emit("player to play", {'player': next_player_to_play, 'allowed_cards': allowed_cards},
                     room=game_id, namespace=NAMESPACE)
                return

            else:
                emit("player to bet", {'player': nplayer, 'allowed_bets': game.allowed_bets(nplayer)}, room=game_id,
                     namespace=NAMESPACE)
                return
        except Exception as e:
            logging.debug("Bet received: " + bet)
            logging.error(e)
            traceback.logging.error_stack()
            emit("alert", "Invalid bet!", room=clients[game_id][username], namespace=NAMESPACE)


def hand_completed(game_id, username):
    game = games[game_id]
    scores = game.update_scores()
    logging.info("hand completed, next player to deal:" + game.next_player_to_deal())
    socketio.emit("hand completed", {'scores': scores, 'bets': game.bets,
                                     'wins': game.wins, 'hand_nb': game._current_hand_nb,
                                     'player_to_deal': game.next_player_to_deal()},
                  room=game_id, namespace=NAMESPACE)
    socketio.emit("player to deal", game.next_player_to_deal(), room=game_id, namespace=NAMESPACE)
    if game.is_game_over():
        socketio.emit("game over", game.get_highest_score_player(), room=game_id, namespace=NAMESPACE)
        logging.debug("Game " + str(game_id) + " is over")
        clean_game_data(game_id)

    elif game.dealing_method == OhellGame.AUTOMATED_DEALING:
        generate_hands(game_id, "")


def next_round(game_id, nplayer, allowed_cards):
    game = games[game_id]
    game.create_round()

    socketio.emit("clear round", room=game_id, namespace=NAMESPACE)
    socketio.emit("player to play", {'player': nplayer, 'allowed_cards': allowed_cards}, room=game_id,
                  namespace=NAMESPACE)

    if game.is_hand_completed():
        hand_completed(game_id, nplayer)


@socketio.on('player played', namespace=NAMESPACE)
def player_played(data):
    logging.info("card played event received")
    game_id = session.get('game_id')
    # Emit event to players so they can see the card that was played
    if game_id is None:
        logging.error("ERROR: Game not found!!!")
    else:
        card = data['data']
        new_data = {'player': session.get('username'), 'card': card}
        emit("card played", new_data, room=game_id, namespace=NAMESPACE)

        game = games[game_id]
        winner = game.card_played(session.get('username'), card)

        nplayer = game.get_active_player()
        if not winner is None:
            # There is a winnder, so round is ended
            allowed_cards = game.get_hand(nplayer).serialize()
            winnning_card = game.get_current_round().cards_played[winner]
            socketio.emit("round ended",
                          {"winner": winner, "card": winnning_card.desc(), "last_player": session['username']},
                          room=game_id,
                          namespace=NAMESPACE)
            timer = threading.Timer(4.0, next_round, [game_id, nplayer, allowed_cards])
            timer.start()
        else:
            # Round continues
            allowed_cards = game.get_allowed_cards(nplayer)
            emit("player to play",
                 {'player': nplayer, 'allowed_cards': allowed_cards, "last_player": session['username']}, room=game_id,
                 namespace=NAMESPACE)

        logging.debug("Allowed cards: " + str(allowed_cards))
    return


@socketio.on('start hand', namespace=NAMESPACE)
def start_hand(nbcards, trump):
    # selection = data["selection"]
    # votes[selection] += 1
    logging.info("start hand event received")
    game_id = session.get('game_id')
    username = session.get('username')

    if game_id is None or username is None:
        logging.error("Error in start_hand. username or game_id not in session")
        return

    generate_hands(game_id, "", int(nbcards), trump)


def generate_hands(game_id, username, nbcards=0, trump=True):
    if not game_id in games:
        # Should never happen
        game = OhellGame();
        games[game_id] = game
    else:
        game = games[game_id]

    hands = game.deal(nbcards, trump, username)
    if hands is None:
        socketio.emit("alert", "Invalid number of card for size of deck", room=clients[game_id][username],
                      namespace=NAMESPACE)
    else:
        round = game.create_round()

        # FInd out who the first player to bet is
        nplayer = game.get_active_player()

        # Distribute cards to each players
        for player in game.get_playing_players():
            cards = hands[player].serialize()
            logging.error("Cards for player " + player + " " + str(cards))
            socketio.emit("new hand", cards, room=clients[game_id][player], namespace=NAMESPACE)

        if trump and not game.trump_card is None:
            socketio.emit("trump card", {"trump_card": str(game.trump_card), "trump_suit": str(game.trump_suit)},
                          room=game_id, namespace=NAMESPACE)

        socketio.emit("player to bet", {'player': nplayer, 'allowed_bets': game.allowed_bets(player)}, room=game_id,
                      namespace=NAMESPACE)
        return


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
            logging.debug("Player: " + player)
            current_client_room = clients[game_id].get(player)

            # Adding new client room id (sid) to list of clients
            clients[game_id][player] = request.sid
            session['sid'] = request.sid
            join_room(game_id)

@socketio.on('join game ai', namespace=NAMESPACE)
def join_ai(data):
    # Note that a refresh on the client side causes the socketio sid to changed
    # so need to remove the previous sid from the room
    logging.info("join_ai")
    session['_fresh'] = False
    session['csrf_token'] = "b7005925b16302affc42642648b2651c2a454b9e"
    session['username'] = data['player']
    session['game_id'] = str(data['game_id'])

    game_id = str(data.get('game_id'))
    logging.debug("game_id: " + repr(game_id))
    logging.debug(str(games.keys()))
    if not game_id is None:
        if game_id in games:
            # Add user to room if user is not there already
            player = data['player']
            logging.debug("Player: " + player)
            current_client_room = clients[game_id].get(player)

            # Adding new client room id (sid) to list of clients
            clients[game_id][player] = request.sid
            session['sid'] = request.sid
            join_room(game_id)

    on_post("Hello there!")

@socketio.on('client post', namespace=NAMESPACE)
def on_post(msg):
    session['csrf_token'] = "b7005925b16302affc42642648b2651c2a454b9e"
    # Just distribute to players in room
    game_id = session.get('game_id')
    logging.debug("In on_post, session: " + repr(session))
    logging.debug("In on_post, msg: " + msg)
    if game_id is None:
        logging.error("NO GAME_ID IN SESSION!!!!")
    else:
        socketio.emit("msg posted", {'sender': session.get('username'), 'msg': msg}, room=game_id, namespace=NAMESPACE)


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

# Add player to a game
def add_player(player,game_id):
    #session['game_id'] = game_id
    game = games.get(game_id)
    if not game is None:
        common_routes.add_player(player, game, NAMESPACE)
        if game.started:
            restart_hand(game_id)


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


def restart_hand(game_id):
    game = games.get(game_id)
    # If manueal dealing, generate player to deal event
    # Othrwise deal another hand
    socketio.emit("alert", "Hand to be restarted", room=game_id, namespace=NAMESPACE)
    if game.dealing_method == OhellGame.MANUAL_DEALING:
        # soc
        # ketio.emit("hand completed", {'scores':game.get_scores(), 'player_to_deal': game.dealer}, room=game_id, namespace=NAMESPACE)
        socketio.emit("player to deal", game.dealer, room=game_id, namespace=NAMESPACE)
    elif game.started:
        game._current_hand_nb = game._current_hand_nb - 1  # Deal again
        generate_hands(game_id, game.dealer)

def clean_game_data(game_id):
    game = games.get(game_id)
    if game is None:
        return
    del games[game_id]
    del clients[game_id]

# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
