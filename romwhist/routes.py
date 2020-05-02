"""
This module implements routes.

author: Philippe Fajeau

"""
from flask import Blueprint
from . import controllers,deck,card,hand
from .game import RomWhistGame
from romwhist import socketio,app
from flask import render_template, request, flash, session, url_for, redirect
from .forms import LoginForm, StartGameForm, JoinGameForm, GameForm, IndexForm
from flask_login import current_user, login_user, logout_user, AnonymousUserMixin
from romwhist.models import User
from romwhist.extensions import db
from flask_socketio import join_room, leave_room
from flask_socketio import SocketIO, emit
from random import randint


# Map of games, key is game id
games = dict()

# Map keyed by game ids and containing list of players for each game id
players = dict()

# Dictionary of session iDs for each game. This is a dictionary of Dictionary
# Keys are game ids and then player ids. Used for socketios.
clients = dict()

# Dictionary of hands for game for each player
# hands = dict()

@app.route("/",methods=['GET', 'POST'])
@app.route("/index",methods=['GET', 'POST'])
def index():

        # print (current_user)
        # if isinstance(current_user, User):
        #     logout_user()
        #     #user = User(username=user_name)
        #     db.session.delete(current_user)
        #     db.session.commit()
        #
        # user = User.query.filter_by(username=user_name).first()
        # print ("User retrieved:", user)
        # if user is None:
            # user = User(username=user_name)
            # db.session.add(user)
            # db.session.commit()
            # login_user(user)
    form = IndexForm()
    if form.validate_on_submit():
        username = form.user_name.data
        print ("User: ", username)
        # Used by client
        session['username'] = username
        if form.join_game.data:
            game_id = request.form['game_id']
            print("game id: ", game_id)
            if not game_id in games:
                error = "This game has not been created yet"
                print(error)
                return render_template('index.html', error = error, form=form)
            if session['username'] in players[game_id]:
                error = "The game already has a user with the same name"
                print(error)
                return render_template('index.html', error = error, form=form)

            # TODO maybe prevent player from joining game in progres
            game = games[game_id]
            session['ownername'] = game.get_owner()
            add_player(game_id)
            return redirect(url_for('game'))

        elif form.start_game.data:
            print("start game")
            if len(games) == 999:
                error = "No more games available!!! Please try again later"
                print(error)
                return render_template('index.html', error = error, form=form)

            game_id = str(randint(1,999))
            while game_id in games:
                game_id = str(randint(1,999))
            print ("game_id:", game_id)

            print("creating new game with id: ", game_id)
            # Add game id in session
            game = RomWhistGame(game_creator=username, deck_size=int(request.form['deck_size']))
            games[game_id] = game
            players[game_id] = []
            clients[game_id] = dict()

            session['ownername'] = username
            add_player(game_id)
            return redirect(url_for('game'))
        # else:
        #     error = "User already exists"
        #     print(error)
        #     return render_template('index.html', error = error, form=form)
    else:
        return render_template("index.html", form=form, error=form.errors)

@app.route("/base")
def base():
    # TODO - add here endpoint of resource where you want to land on page load. e.g.
    # return redirect(url_for("auth_blueprint.home"))
    return render_template("base.html")


@app.route("/game", methods=['GET', 'POST'])
def game():
    print("In game route")
    form=GameForm()
    player = session.get('username')
    if player is None:
        flash("Session has expired")
        return redirect(url_for('index'))

    game_id = session.get('game_id')
    if game_id is None:
        flash("Game does not exist")
        return redirect(url_for('index'))

    game=games.get(game_id);
    if game is None:
        flash("Game does not exist")
        return redirect(url_for('index'))

    if request.method == 'POST':
        if game_id is None:
            error = "Could not find game_id in session"
            print(error)
            return render_template('index.html', error = error, form=IndexForm())

        if form.stop_game.data:
            stop_game()
            return redirect(url_for('index'))

        if form.leave_game.data:
            remove_player()
            return redirect(url_for('index'))

    else:
        hand = game.get_hands().get(player)
        if hand is None:
            hand=[]
        else:
            hand = hand.serialize()
        return render_template("game.html", form=form,  players=players[game_id], scores=game.get_scores(), \
        hand=hand, bets=game.get_bets(), wins=game.get_wins(), active_player=game.get_active_player())

# @app.route("/login",methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
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
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

# @app.route("/logout",methods=['GET', 'POST'])
def logout():
    remove_player()
    logout_user()
    return redirect(url_for('login'))

@socketio.on('message')
def message(data):
    print ("message received");

@socketio.on("cs game started")
def game_started():
    game_id = session.get('game_id')
    if not game_id is None:
        game = games.get(game_id)
        if not game is None:
            # TODO:
            # If manual dealiing, just emit event game sc game started
            # In automated dealing, call start_hands with computed nb of cards and trump
            # In case it is a restart
            game.reset()
            player = players[game_id][randint(0,len(players[game_id])-1)]
            socketio.emit("sc game started", {'player_to_deal': player, 'nb_cards': 0}, room=game_id)

            # TODO: if automated dealing, need to create hands
            if games[game_id].dealing_method == RomWhistGame.AUTOMATED_DEALING:
                start_hand(game.get_nb_cards_to_deal(), game.get_play_with_trump())
    #

@socketio.on("player bet")
def player_bet(bet):
    print ("player bet event received")
    print ("Player bet: " + bet)
    game_id = session.get('game_id')
    if game_id is None:
        print("ERROR: Game not found!!!")
    else:
        # If all players have bet, enable next player to play
        game = games[game_id]
        game.place_bet(session['username'], int(bet))
        emit("player bet", {'player':session['username'], 'bet':bet}, room = game_id)
        nplayer = game.next_player_to_bet(session['username'])
        if nplayer is None:
            # next_player_to_play = next_player(session['username'], players[game_id])
            next_player_to_play = game.get_active_player()
            # All cards allowed for first player
            allowed_cards = game.get_hand(next_player_to_play).serialize()
            print("Allowed cards: ", allowed_cards)
            emit("player to play", {'player': next_player_to_play, 'allowed_cards':allowed_cards}, room=game_id)

        # Last player to bet
        else:
            forbidden_bet = game.forbidden_bet(nplayer)
            print ("Forbidden bet for player " + nplayer + " is:" + str(forbidden_bet))
            emit("player to bet", {'player': nplayer, 'forbidden_bet':forbidden_bet}, room=game_id)
    return

@socketio.on('player played')
def player_played(data):
    print ("card played event received")
    game_id = session.get('game_id')
    # Emit event to players so they can see the card that was played
    if game_id is None:
        print("ERROR: Game not found!!!")
    else:
        card = data['data']
        new_data = {'player': session['username'], 'card': card}
        emit("card played", new_data, room=game_id)

        game = games[game_id]
        winner = game.card_played(session['username'], card)
        if not winner is None:
            emit("round ended", winner, room=game_id)
            game.create_round()
            # nplayer = winner
            nplayer = game.get_active_player()
            allowed_cards = game.get_hand(nplayer).serialize()

            if game.is_hand_completed():
                scores = game.update_scores()
                print ("hand completed, next player to deal:", game.next_player_to_deal())
                emit("hand completed", {'scores':scores, 'player_to_deal': game.next_player_to_deal()}, room=game_id)
        else:
            # nplayer = next_player(session['username'], players[game_id])
            nplayer = game.get_active_player()
            allowed_cards = game.get_allowed_cards(nplayer)

        print("Allowed cards: ", allowed_cards)
        emit("player to play", {'player':nplayer, 'allowed_cards':allowed_cards}, room=game_id)
    return

@socketio.on('start hand')
def start_hand(nbcards, trump):
    #selection = data["selection"]
    #votes[selection] += 1
    print ("start hand event received")
    generate_hands(int(nbcards), trump)

def generate_hands(nbcards, trump):
    print (nbcards)
    print("Trump:", trump)

    game_id = session.get('game_id')

    if not game_id in games:
       # Should never happen
        game = RomWhistGame();
        games[game_id] = game
    else:
        game = games[game_id]

    hands = game.deal(nbcards, trump, session['username'])
    if hands is None:
        socketio.emit("alert", "Invalid number of card for size of deck", room=clients[game_id][session['username']])
    else:
        round = game.create_round()

        # FInd out who the first player to bet is
        nplayer = game.get_active_player()
        # nplayer = next_player(session['username'], players[game_id])

        # Distribute cards to each players
        for player in players[game_id]:
            cards = hands[player].serialize()
            print ("Cards for player ", player, " ", cards)
            socketio.emit("new hand", cards, room=clients[game_id][player])

        if trump:
            socketio.emit("trump card", str(game.trump_card), room=game_id)

        socketio.emit("player to bet", {'player': nplayer, 'forbidden_bet':-1}, room=game_id)

@socketio.on('join game')
def on_join(data):
    # Note that a refresh on the client side causes the socketio sid to changed
    # so need to remove the previous sid from the room
    print ("on_join")
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

@socketio.on('leave game')
def on_leave(data):
    game_id = session.get('game_id')
    if game_id is None:
        print("NO GAME_ID IN SESSION!!!!")
        # TODO: may have a case where the session has been cleared already
        # (user logged out). In this case how to remove user from room?
    else:
        leave_room(game_id)

@socketio.on('stop game')
def on_stop(data):
    game_id = session.get('game_id')
    if game_id is None:
        print("NO GAME_ID IN SESSION!!!!")
        # TODO: may have a case where the session has been cleared already
        # (user logged out). In this case how to remove user from room?
    else:
        leave_room(game_id)
        emit("game stopped", session['username'], room=game_id)

@socketio.on('client post')
def on_post(msg):
    # Just distribute to players in room
    game_id = session.get('game_id')
    if game_id is None:
        print("NO GAME_ID IN SESSION!!!!")
        # TODO: may have a case where the session has been cleared already
        # (user logged out). In this case how to remove user from room?
    else:
        emit("msg posted", {'sender': session['username'], 'msg': msg}, room=game_id)


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected')

def stop_game():
    game_id = session.get('game_id')
    if game_id is None:
        print("NO GAME_ID IN SESSION!!!!")
        return
        # TODO: may have a case where the session has been cleared already
        # (user logged out). In this case how to remove user from room?
    if not games.get(game_id) is None:
        del games[game_id]
        del clients[game_id]
        del players[game_id]
        socketio.emit("game stopped", session['username'], room=game_id)
        return

# Added a player to a game
def add_player(game_id):
    session['game_id'] = game_id
    players[game_id].append(session['username'])
    games[game_id].add_player(session['username'])
    # send(session['username'] + ' has joined game', room=game_id)
    socketio.emit("new player", session['username'], room=game_id)


def remove_player():
    game_id = session.get('game_id')
    if not game_id is None:
        if game_id in players:
            username = session['username']
            players[game_id].remove(username)
            games[game_id].remove_player(username)
        if username in clients[game_id]:
            del clients[game_id][username]

        socketio.emit("player left", username, room=game_id)

def next_player(player, list_players):
    pos = list_players.index(player)
    if pos == len(list_players)-1:
        return list_players[0]
    else:
        return list_players[pos+1]
# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
