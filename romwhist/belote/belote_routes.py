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

# Map of games, key is game id
games = dict()

# Dictionary of session iDs for each game. This is a dictionary of Dictionary
# Keys are game ids and then player ids. Used for socketio.
bel_clients = dict()


# @app.route("/belote_start",methods=['GET', 'POST'])
def belote_start():
    form = BeloteStartForm()
    if form.validate_on_submit():
        # Sanitize the username (as it isued as IDs in the html)
        username = unidecode.unidecode(form.user_name.data)
        username = username.replace(" ", "")
        logging.debug("User: " + username)

        # Used by client
        previous_alias = session.get('username')

        session['username'] = username
        if form.join_game.data:
            game_id = request.form['game_id']
            logging.debug("game id: ", game_id)
            if not game_id in games:
                error = "This game has not been created yet"
                logging.error(error)
                return render_template('belote_start.html', error=error, form=form)

            game = games[game_id]
            # Not allowed to connect if another player has the same alias
            # and game has not started. If game has started, assume player
            # is trying to reconnect after having lost a connection
            if username in game.get_players() and not game.started:
                error = "The game already has a user with the same name"
                logging.error(error)
                return render_template('belote_start.html', error=error, form=form)

            # Not allowed to connect to a game already started unless the player
            # is already an existing player (same alias)
            if game.started and not username in game.get_players():
                error = "This game has already started! You cannot join a game in progress"
                logging.error(error)
                return render_template('belote_start.html', error=error, form=form)

            # Remove player from game if that player was already in the games
            # if previous_alias in players[game_id]:
            #     remove_player(game_id, previous_alias)

            session['ownername'] = game.owner
            add_player(game_id)
            return redirect(url_for('belote_play'))

        elif form.start_game.data:
            logging.info("start game")
            if len(games) == 999:
                error = "No more games available!!! Please try again later"
                logging.error(error)
                return render_template('belote_start.html', error=error, form=form)

            game_id = str(randint(1, 999))
            while game_id in games:
                game_id = str(randint(1, 999))
            logging.info("game_id:" + str(game_id))

            points_to_reach = int(form.points_to_reach.data)

            logging.info("creating new game with id: " + str(game_id))
            # Add game id in session
            game = BeloteGame(game_creator=username, id=game_id)
            game.win_game_points = points_to_reach

            games[game_id] = game
            # players[game_id] = []
            bel_clients[game_id] = dict()

            # dealing_method = request.form['dealing_method']
            # logging.info ("In route game, dealing method is: ", request.form['dealing_method'])
            dealing_method = "computer"
            session['ownername'] = username
            add_player(game_id)
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
            stop_game()
            return redirect(url_for('belote_start'))
            # return redirect(url_for('game'))

        # if "leave_game" in request.form:
        if request.form['action_game'] == "leave_game":
            remove_player(game_id, session['username'])
            return redirect(url_for('belote_start'))

        if request.form['action_game'] == "remove_player":
            logging.info("Remve Player button pressed")
            rplayer = request.form['player_list']
            logging.info("Player to remove: ", rplayer)

            remove_player(game_id, rplayer)
            return redirect(url_for('belote_play'))
            # get user that needs to be removed
            # remove user
            # re-distribute and display game page

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
            socketio.emit("sc game started", {'player_to_deal': player, 'nb_cards': 5}, room=game_id,
                          namespace=NAMESPACE)

            generate_hands(game_id, player)


@socketio.on("player bet", namespace=NAMESPACE)
def player_bet(bet):
    logging.info("player bet event received")
    logging.info("Player bet: " + bet)
    username = session['username']
    game_id = session.get('game_id')
    if game_id is None:
        logging.error("ERROR: Game not found!!!")
    else:
        game = games[game_id]
        if game.phase == BeloteGame.GamePhase.BET or game.phase == BeloteGame.GamePhase.BET2:
            game = games[game_id]
            try:
                game.place_bet(session['username'], bet)
                emit("player bet", {'player': session['username'], 'bet': bet}, room=game_id, namespace=NAMESPACE)
                nplayer = game.get_active_player()
                if game.phase == BeloteGame.GamePhase.DEAL:
                    common_routes.restart_hand(game_id, NAMESPACE)

                elif game.phase == BeloteGame.GamePhase.BET or game.phase == BeloteGame.GamePhase.BET2:
                    emit("player to bet", {'player': nplayer, 'allowed_bets': game.allowed_bets(nplayer)}, room=game_id,
                         namespace=NAMESPACE)

                elif game.phase == BeloteGame.GamePhase.PLAY:
                    hands = game.deal_2(game.dealer)
                    logging.debug("After deal_2")
                    round = game.create_round()
                    # Distribute cards to each players
                    for player in game.get_playing_players():
                        cards = hands[player].serialize()
                        logging.debug("Cards for player " + player + " " + str(cards))
                        socketio.emit("new hand", cards, room=bel_clients[game_id][player], namespace=NAMESPACE)
                    next_player_to_play = game.get_active_player()
                    allowed_cards = game.get_hand(next_player_to_play).serialize()
                    logging.debug("Allowed cards: " + str(allowed_cards))
                    logging.debug("Player to play: " + next_player_to_play)
                    emit("trump suit", game.trump_suit, room=game_id, namespace=NAMESPACE)
                    emit("player to play", {'player': next_player_to_play, 'allowed_cards': allowed_cards},
                         room=game_id, namespace=NAMESPACE)
                    player_belote = game.player_with_belote
                    if (not player_belote is None):
                        logging.debug("Player with Belote / Rebelote: " + player_belote)
                        emit("belote rebelote enabled", player_belote, room=bel_clients[game_id][player_belote],
                             namespace=NAMESPACE)
                return
            except Exception as e:
                logging.debug("Bet received: " + str(bet))
                logging.error(e)
                traceback.print_stack()
                emit("alert", "Error in place bet", room=bel_clients[game_id][username], namespace=NAMESPACE)


def hand_completed(game_id, username):
    game = games[game_id]
    game.hand_completed()
    scores = game.get_scores()
    logging.info("hand completed, next player to deal:" + game.next_player_to_deal())
    socketio.emit("hand completed", {'scores': scores, 'wins': game.hand_points,
                                     'hand_nb': game._current_hand_nb, 'player_to_deal': game.next_player_to_deal(),\
                                     'winners': game.hand_winner},
                  room=game_id, namespace=NAMESPACE)
    socketio.emit("player to deal", game.next_player_to_deal(), room=game_id, namespace=NAMESPACE)
    if game.is_game_over():
        socketio.emit("game over", game.get_highest_score_player(), room=game_id, namespace=NAMESPACE)
    else:
        generate_hands(game_id, "")


def next_round(game_id, nplayer, allowed_cards):
    game = games[game_id]
    game.create_round()

    socketio.emit("clear round", room=game_id, namespace=NAMESPACE)
    socketio.emit("player to play", {'player': nplayer, 'allowed_cards': allowed_cards},
                  room=game_id, namespace=NAMESPACE)

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
        new_data = {'player': session['username'], 'card': card}
        emit("card played", new_data, room=game_id, namespace=NAMESPACE)

        game = games[game_id]
        winner = game.card_played(session['username'], card)

        check_belote_played(game_id, session['username'])
        nplayer = game.get_active_player()

        if winner is None:
            # Round continues
            allowed_cards = game.get_allowed_cards(nplayer)
            emit("player to play", {'player': nplayer, 'allowed_cards': allowed_cards}, room=game_id,
                 namespace=NAMESPACE)
        else:
            # There is a winnder, so round is ended
            # game.round_ended(winner)
            allowed_cards = game.get_hand(nplayer).serialize()
            winnning_card = game.get_current_round().cards_played[winner]
            emit("round ended", {"winner": winner, "card": winnning_card.desc(), "last_player": session['username'],
                 "points":game.hand_points}, room=game_id, namespace=NAMESPACE)
            timer = threading.Timer(4.0, next_round, [game_id, nplayer, allowed_cards])
            timer.start()

        # Belote/rebelote status

        logging.info("Allowed cards: " + str(allowed_cards))


def check_belote_played(game_id, player):
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


# TODO factorize with ohell
def generate_hands(game_id, username, nbcards=5, trump=True):
    if not game_id in games:
        # Should never happen
        game = BeloteGame();
        games[game_id] = game
    else:
        game = games[game_id]

    hands = game.deal_1(username)

    # FInd out who the first player to bet is
    nplayer = game.get_active_player()

    # Distribute cards to each players
    for player in game.get_playing_players():
        cards = hands[player].serialize()
        logging.info("Cards for player " + player + " " + str(cards))
        socketio.emit("new hand", cards, room=bel_clients[game_id][player], namespace=NAMESPACE)

    socketio.emit("trump card", {"trump_card": str(game.trump_card), "trump_suit": str(game.trump_suit)}, room=game_id,
                  namespace=NAMESPACE)
    socketio.emit("player to bet", {'player': nplayer, 'allowed_bets': game.allowed_bets(nplayer)}, room=game_id,
                  namespace=NAMESPACE)
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
        emit("belote announced", {'player': player, 'announced': announce}, room=game_id, namespace=NAMESPACE)
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
            current_client_room = bel_clients[game_id].get(player)

            # Adding new client room id (sid) to list of clients
            bel_clients[game_id][player] = request.sid
            session['sid'] = request.sid
            join_room(game_id)


@socketio.on('client post', namespace=NAMESPACE)
def on_post(msg):
    # Just distribute to players in room
    common_routes.post_msg(msg, session['username'], session.get('game_id'), NAMESPACE)


@socketio.on('disconnect', namespace=NAMESPACE)
def test_disconnect():
    logging.info('Client disconnected. ', session['username'])
    client_id = request.sid
    player = session['username']
    game_id = session['game_id']
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
    players = bel_clients.get(game_id)
    if players is None:
        return

    # if player in players:
    #     current_client_id = clients[game_id][player]
    #     if current_client_id == client_id:
    # remove_player(game_id, player)


def stop_game():
    game_id = session.get('game_id')
    if game_id is None:
        logging.error("NO GAME_ID IN SESSION!!!!")
        return

    game = games.get(game_id)
    if game is None:
        logging.error("Game does not exist")
        return

    if game.is_game_over():
        socketio.emit("game over", games.get(game_id).get_highest_score_player(), room=game_id, namespace=NAMESPACE)
        del games[game_id]
        del clients[game_id]
        return


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
def add_player(game_id):
    session['game_id'] = game_id
    common_routes.add_player(session['username'], games[game_id], NAMESPACE)


def remove_player(game_id, player):
    # game_id = session.get('game_id')
    if not game_id is None:
        game = games.get(game_id)
        if not game is None:
            if game.started:
                game.disable_player(player)
            else:
                game.remove_player(player)
                if player in bel_clients[game_id]:
                    del bel_clients[game_id][player]

        socketio.emit("player left", player, room=game_id, namespace=NAMESPACE)
        socketio.emit("clear round", room=game_id, namespace=NAMESPACE)
        common_routes.restart_hand(game_id, NAMESPACE)

# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
