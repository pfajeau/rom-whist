"""
This module implements routes.

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
from romwhist import controllers,deck,card,hand
from romwhist.belote.belote import BeloteGame
from romwhist import socketio,app
from romwhist.forms import LoginForm, StartForm, GameForm
from romwhist.models import User
from romwhist.extensions import db

NAMESPACE='/belote'

# Map of games, key is game id
bel_games = dict()

# Dictionary of session iDs for each game. This is a dictionary of Dictionary
# Keys are game ids and then player ids. Used for socketio.
bel_clients = dict()

# @app.route("/belote_start",methods=['GET', 'POST'])
def belote_start():

    form = StartForm()
    if form.validate_on_submit():
        # Sanitize the username (as it isued as IDs in the html)
        username = unidecode.unidecode(form.user_name.data)
        username = username.replace(" ","")
        print ("User: ", username)

        # Used by client
        previous_alias = session.get('username')

        session['username'] = username
        if form.join_game.data:
            game_id = request.form['game_id']
            print("game id: ", game_id)
            if not game_id in bel_games:
                error = "This game has not been created yet"
                print(error)
                return render_template('belote_start.html', error = error, form=form)

            game = bel_games[game_id]
            # Not allowed to connect if another player has the same alias
            # and game has not started. If game has started, assume player
            # is trying to reconnect after having lost a connection
            if username in game.get_players() and not game.game_started():
                error = "The game already has a user with the same name"
                print(error)
                return render_template('belote_start.html', error = error, form=form)

            # Not allowed to connect to a game already started unless the player
            # is already an existing player (same alias)
            if game.game_started() and not username in game.get_players():
                error = "This game has already started! You cannot join a game in progress"
                print(error)
                return render_template('belote_start.html', error = error, form=form)

            # Remove player from game if that player was already in the games
            # if previous_alias in players[game_id]:
            #     remove_player(game_id, previous_alias)

            session['ownername'] = game.get_owner()
            add_player(game_id)
            return redirect(url_for('belote_play'))

        elif form.start_game.data:
            print("start game")
            if len(bel_games) == 999:
                error = "No more games available!!! Please try again later"
                print(error)
                return render_template('belote_start.html', error = error, form=form)

            game_id = str(randint(1,999))
            while game_id in bel_games:
                game_id = str(randint(1,999))
            print ("game_id:", game_id)

            print("creating new game with id: ", game_id)
            # Add game id in session
            game = BeloteGame(game_creator=username)
            bel_games[game_id] = game
            #players[game_id] = []
            bel_clients[game_id] = dict()

            # dealing_method = request.form['dealing_method']
            # print ("In route game, dealing method is: ", request.form['dealing_method'])
            dealing_method = "computer"
            session['ownername'] = username
            add_player(game_id)
            return redirect(url_for('belote_play'))
    else:
        return render_template("belote_start.html", form=form, error=form.errors)


# @app.route("/belote_play", methods=['GET', 'POST'])
def belote_play():
    print("In belote_play route")
    form=GameForm()
    player = session.get('username')
    if player is None:
        flash("Session has expired")
        return redirect(url_for('belote_start'))

    game_id = session.get('game_id')
    if game_id is None:
        flash("Game does not exist")
        return redirect(url_for('belote_start'))

    game=bel_games.get(game_id);
    if game is None:
        flash("Game does not exist")
        return redirect(url_for('belote_start'))

    if request.method == 'POST':
        # print (request.form)
        if game_id is None:
            error = "Could not find game_id in session"
            print(error)
            return render_template('belote_start.html', error = error)

        # if "stop_game" in request.form:
        if request.form['action_game'] == "stop_game":
            stop_game()
            return redirect(url_for('belote_start'))
            #return redirect(url_for('game'))

        # if "leave_game" in request.form:
        if request.form['action_game'] == "leave_game":
            remove_player(game_id, session['username'])
            return redirect(url_for('belote_start'))

        if request.form['action_game'] == "remove_player":
            print("Remve Player button pressed")
            rplayer = request.form['player_list']
            print ("Player to remove: ", rplayer)

            remove_player(game_id, rplayer)
            return redirect(url_for('belote_play'))
            # get user that needs to be removed
            # remove user
            # re-distribute and display game page

    else:
        hand = game.get_hands().get(player)
        if hand is None:
            hand=[]
        else:
            hand = hand.serialize()
        round = game.get_current_round()
        cards_played = []
        if not round is None:
            cards_played = round.get_cards_played()

        print("Active Player: ", game.get_active_player())
        print("Game Phase: ", game.get_game_phase().name)
        active_player = game.get_active_player()

        print ("Scoresheet:")
        for i in range(game._current_hand_nb-1):
            print (i, " ",game.scoresheet[i][0])
            print (i, " ",game.scoresheet[i][1])
            print (i, " ",game.scoresheet[i][2])

        return render_template("belote.html", form=form,  players=game.get_playing_players(), scores=game.get_scores(), \
        hand=hand,  wins=game.get_wins(), bets = game.get_bets(), active_player=active_player, \
        cards_played=cards_played, allowed_cards=game.get_allowed_cards(active_player), \
        trump=game.trump_card, trump_suit = game.trump_suit, allowed_bets=game.allowed_bets(player), \
        game_phase=game.get_game_phase().name, scoresheet=game.scoresheet)


# @app.route("/login",methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('belote_start'))
    form = LoginForm()
    if form.validate_on_submit():
        print("User name from form:", form.username.data)
        user = User.query.filter_by(username=form.username.data).first()
        if user is None:
            user = User(username=form.username.data)
            db.session.add(user)
            db.session.commit()
        login_user(user, remember=form.remember_me.data)
        print ("current user: ", session['username'])
        return redirect(url_for("belote_start"))
    return render_template('login.html', title='Sign In', form=form)

# @app.route("/logout",methods=['GET', 'POST'])
# def logout():
#     remove_player()
#     logout_user()
#     return redirect(url_for('login'))

@socketio.on('message', namespace=NAMESPACE)
def message(data):
    print ("message received");

@socketio.on("cs game started", namespace=NAMESPACE)
def game_started():
    game_id = session.get('game_id')
    if not game_id is None:
        game = bel_games.get(game_id)
        if not game is None:
            # In automated dealing, call start_hands with computed nb of cards and trump
            # In case it is a restart
            game.reset()
            game.start_game()
            player = game.get_playing_players()[randint(0,len(game.get_playing_players())-1)]
            socketio.emit("sc game started", {'player_to_deal': player, 'nb_cards': 5}, room=game_id, namespace=NAMESPACE)

            generate_hands(game_id, player)


@socketio.on("player bet", namespace=NAMESPACE)
def player_bet(bet):
    print ("player bet event received")
    print ("Player bet: " + bet)
    username = session['username']
    game_id = session.get('game_id')
    if game_id is None:
        print("ERROR: Game not found!!!")
    else:
        game = bel_games[game_id]
        if game.get_game_phase()==BeloteGame.GamePhase.BET or game.get_game_phase()==BeloteGame.GamePhase.BET2:
            game = bel_games[game_id]
            try:
                game.place_bet(session['username'], bet)
                emit("player bet", {'player':session['username'], 'bet':bet}, room = game_id, namespace=NAMESPACE)
                nplayer = game.get_active_player()
                if game.get_game_phase() == BeloteGame.GamePhase.DEAL:
                    restart_hand(game_id)

                elif game.get_game_phase() == BeloteGame.GamePhase.BET or game.get_game_phase() == BeloteGame.GamePhase.BET2:
                    emit("player to bet", {'player': nplayer, 'allowed_bets': game.allowed_bets(nplayer)}, room=game_id,namespace=NAMESPACE)

                elif game.get_game_phase() == BeloteGame.GamePhase.PLAY:
                    hands = game.deal_2(game.dealer)
                    print ("After deal_2")
                    round = game.create_round()
                    # Distribute cards to each players
                    for player in game.get_playing_players():
                        cards = hands[player].serialize()
                        print("Cards for player ", player, " ", cards)
                        socketio.emit("new hand", cards, room=bel_clients[game_id][player], namespace=NAMESPACE)
                    next_player_to_play = game.get_active_player()
                    allowed_cards = game.get_hand(next_player_to_play).serialize()
                    print("Allowed cards: ", allowed_cards)
                    print ("Player to play: ", next_player_to_play)
                    emit("trump suit", game.trump_suit,  room=game_id, namespace=NAMESPACE)
                    emit("player to play", {'player': next_player_to_play, 'allowed_cards':allowed_cards}, room=game_id, namespace=NAMESPACE)
                return
            except Exception as e:
                print ("Bet received: ", bet)
                print (e)
                traceback.print_stack()
                emit("alert", "Invalid bet!", room=bel_clients[game_id][username], namespace=NAMESPACE)

def hand_completed(game_id, username):
    game = bel_games[game_id]
    game.hand_completed()
    scores = game.get_scores()
    print ("hand completed, next player to deal:", game.next_player_to_deal())
    socketio.emit("hand completed", {'scores':scores,'wins': game.wins,
                                     'hand_nb': game._current_hand_nb, 'player_to_deal': game.next_player_to_deal()},
                  room=game_id, namespace=NAMESPACE)
    socketio.emit("player to deal", game.next_player_to_deal(), room=game_id, namespace=NAMESPACE)
    if game.is_game_over():
        socketio.emit("game over", game.get_highest_score_player(), room=game_id, namespace=NAMESPACE)
    else:
        generate_hands(game_id, "")

def next_round(game_id, nplayer,allowed_cards):
    game = bel_games[game_id]
    game.create_round()

    socketio.emit("clear round",room=game_id, namespace=NAMESPACE)
    socketio.emit("player to play", {'player':nplayer, 'allowed_cards':allowed_cards},
                  room=game_id, namespace=NAMESPACE)

    if game.is_hand_completed():
        hand_completed(game_id, nplayer)


@socketio.on('player played', namespace=NAMESPACE)
def player_played(data):
    print ("card played event received")
    game_id = session.get('game_id')
    # Emit event to players so they can see the card that was played
    if game_id is None:
        print("ERROR: Game not found!!!")
    else:
        card = data['data']
        new_data = {'player': session['username'], 'card': card}
        emit("card played", new_data, room=game_id, namespace=NAMESPACE)

        game = bel_games[game_id]
        winner = game.card_played(session['username'], card)
        nplayer = game.get_active_player()

        if  winner is None:
            # Round continues
            allowed_cards = game.get_allowed_cards(nplayer)
            emit("player to play", {'player': nplayer, 'allowed_cards': allowed_cards}, room=game_id,
                 namespace=NAMESPACE)
        else:
            # There is a winnder, so round is ended
            # game.round_ended(winner)
            allowed_cards = game.get_hand(nplayer).serialize()
            winnning_card = game.get_current_round().cards_played[winner]
            socketio.emit("round ended", {"winner": winner, "card": winnning_card.desc()}, room=game_id, namespace=NAMESPACE)
            timer = threading.Timer(4.0, next_round, [game_id, nplayer,allowed_cards])
            timer.start()

        print("Allowed cards: ", allowed_cards)

    return

@socketio.on('start hand', namespace=NAMESPACE)
def start_hand(nbcards, trump):
    #selection = data["selection"]
    #votes[selection] += 1
    print ("start hand event received")
    game_id = session.get('game_id')
    username = session.get('username')

    if game_id is None or username is None:
        print("Error in start_hand. username or game_id not in session")
        return

    generate_hands(game_id, "", int(nbcards), trump)

# TODO factorize with ohell
def generate_hands(game_id, username, nbcards=5, trump=True):
    print (nbcards)

    if not game_id in bel_games:
       # Should never happen
        game = BeloteGame();
        bel_games[game_id] = game
    else:
        game = bel_games[game_id]

    hands = game.deal_1(username)

    # FInd out who the first player to bet is
    nplayer = game.get_active_player()

    # Distribute cards to each players
    for player in game.get_playing_players():
        cards = hands[player].serialize()
        print ("Cards for player ", player, " ", cards)
        socketio.emit("new hand", cards, room=bel_clients[game_id][player], namespace=NAMESPACE)

    socketio.emit("trump card", {"trump_card": str(game.trump_card), "trump_suit": str(game.trump_suit)}, room=game_id, namespace=NAMESPACE)
    socketio.emit("player to bet", {'player': nplayer, 'allowed_bets':game.allowed_bets(nplayer)}, room=game_id, namespace=NAMESPACE)
    return

@socketio.on('join game', namespace=NAMESPACE)
def on_join(data):
    # Note that a refresh on the client side causes the socketio sid to changed
    # so need to remove the previous sid from the room
    print ("on_join")
    game_id = session.get('game_id')
    if not game_id is None:
        if session['game_id'] in bel_games:
            # Add user to room if user is not there already
            player = session.get('username')
            current_client_room = bel_clients[game_id].get(player)

            # Adding new client room id (sid) to list of clients
            bel_clients[game_id][player] = request.sid
            session['sid'] = request.sid
            join_room(game_id)

@socketio.on('stop game', namespace=NAMESPACE)
def on_stop(data):
    game_id = session.get('game_id')
    if game_id is None:
        print("NO GAME_ID IN SESSION!!!!")
        # TODO: may have a case where the session has been cleared already
        # (user logged out). In this case how to remove user from room?
    else:
        leave_room(game_id)
        emit("game stopped", session['username'], room=game_id, namespace=NAMESPACE)

@socketio.on('client post', namespace=NAMESPACE)
def on_post(msg):
    # Just distribute to players in room
    game_id = session.get('game_id')
    if game_id is None:
        print("NO GAME_ID IN SESSION!!!!")
    else:
        emit("msg posted", {'sender': session['username'], 'msg': msg}, room=game_id, namespace=NAMESPACE)


@socketio.on('disconnect', namespace=NAMESPACE)
def test_disconnect():
    print('Client disconnected. ', session['username'])
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
            #remove_player(game_id, player)


def stop_game():
    game_id = session.get('game_id')
    if game_id is None:
        print("NO GAME_ID IN SESSION!!!!")
        return
    if not bel_games.get(game_id) is None:
        socketio.emit("game over", bel_games.get(game_id).get_highest_score_player(), room=game_id, namespace=NAMESPACE)
        # socketio.emit("game stopped", session['username'], room=game_id, namespace=NAMESPACE)

        del bel_games[game_id]
        del bel_clients[game_id]
        #del players[game_id]
        return

# Add player to a game
def add_player(game_id):
    session['game_id'] = game_id

    bel_games[game_id].add_player(session['username'])
    socketio.emit("new player", session['username'], room=game_id, namespace=NAMESPACE)
    restart_hand(game_id)


def remove_player(game_id, player):
    # game_id = session.get('game_id')
    if not game_id is None:
        game = bel_games.get(game_id)
        if not game is None:
            if game.game_started():
                game.disable_player(player)
            else:
                game.remove_player(player)
                if player in bel_clients[game_id]:
                    del bel_clients[game_id][player]

        socketio.emit("player left", player, room=game_id, namespace=NAMESPACE)
        socketio.emit("clear round",room=game_id, namespace=NAMESPACE)
        restart_hand(game_id)

def restart_hand(game_id):
    game = bel_games.get(game_id)
    # Deal another hand
    socketio.emit("alert", "Hand to be replayed", room=game_id, namespace=NAMESPACE)
    if game.game_started():
      game._current_hand_nb = game._current_hand_nb - 1  # Deal again
      generate_hands(game_id, "")

# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
