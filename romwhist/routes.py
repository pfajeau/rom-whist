"""
This module implements routes.

author: Philippe Fajeau

"""
from flask import Blueprint
from . import controllers,deck,card,hand
from .utils import Serializer
from .game import RomWhistGame
from romwhist import socketio,app
from flask import render_template, request, flash, session, url_for, redirect
from .forms import LoginForm, StartGameForm, JoinGameForm, GameForm, IndexForm
from flask_login import current_user, login_user, logout_user, AnonymousUserMixin
from romwhist.models import User
from romwhist.extensions import db
from flask_socketio import join_room, leave_room
from flask_socketio import SocketIO, emit

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
    # TODO - add here endpoint of resource where you want to land on page load. e.g.
    # return redirect(url_for("auth_blueprint.home"))
    form = IndexForm()
    if isinstance(current_user, User):
        form.user_name.data=current_user.username

    if form.validate_on_submit():
        print("Index Validate on Submit")
        user_name = form.user_name.data
        print (current_user)
        if isinstance(current_user, User):
            logout_user()
            #user = User(username=user_name)
            db.session.delete(current_user)
            db.session.commit()

        user = User.query.filter_by(username=user_name).first()
        print ("User retrieved:", user)
        if user is None:
            user = User(username=user_name)
            db.session.add(user)
            db.session.commit()
            login_user(user)
            print ("current user: ", current_user.username)
            # Used by client
            session['username'] = current_user.username
            if form.start_game.data:
                print("REdirecting to start game")
                return redirect(url_for('start_game'))
            elif form.join_game.data:
                print("REdirecting to join game")
                return redirect(url_for('join_game'))
        else:
            error = "User already exists"
            print(error)
            return render_template('index.html', error = error, form=form)
    else:
        return render_template("index.html", form=form)

@app.route("/base")
def base():
    # TODO - add here endpoint of resource where you want to land on page load. e.g.
    # return redirect(url_for("auth_blueprint.home"))
    return render_template("base.html")

@app.route("/startgame",methods=['GET', 'POST'])
def start_game():
    print("Current User: ", current_user.username)
    if current_user.is_authenticated:
        form = StartGameForm()
        if form.validate_on_submit():
            game_id = form.game_id.data
            if not game_id in games:
                print("creating new game with id: ", game_id)
                # Add game id in session
                games[game_id] = RomWhistGame()
                players[game_id] = []
                clients[game_id] = dict()
                add_player(game_id)
                return redirect(url_for('game'))
                #return render_template('game.html', title='Bla', form=GmeForm())
            else:
                error = "This game already exists"
                print(error)
                return render_template('start_game.html', error = error, form=form)
        else:
            return render_template('start_game.html', title='Bla', form=form)
    else:
        #form = LoginForm()
        return redirect(url_for('index'))
        #return render_template('login.html', title='Sign In', form=form)

@app.route("/joingame",methods=['GET', 'POST'])
def join_game():
    if current_user.is_authenticated:
        form = JoinGameForm()
        if form.validate_on_submit():

            print("Current User: ", current_user.username)
            game_id = request.form['game_id']
            print("game id: ", game_id)
            # Add player to session. TODO: should check whehter user is already in list
            if not game_id in games:
                error = "This game has not been created yet"
                print(error)
                return render_template('join_game.html', error = error, form=form)
            if current_user.username in players[game_id]:
                error = "The game already has a user with the same name"
                print(error)
                return render_template('join_game.html', error = error, form=form)

            add_player(game_id)
            return redirect(url_for('game'))
            #return render_template('game.html', title='Bla')
#            return render_template('join_game.html', title='Bla', form=form)
        else:
            return render_template('join_game.html', title='Bla', form=form)
    else:
        return redirect(url_for('login'))
#        form = LoginForm()
#        return render_template('login.html', title='Sign In', form=form)

@app.route("/game", methods=['GET', 'POST'])
def game():
    form = GameForm()
    game_id = session.get('game_id')
    if game_id is None:
        error = "Could not find game_id in session"
        print(error)
        return render_template('join_game.html', error = error, form=JoinGameForm())
    else:
        return render_template("game.html", form=form,  players=players[game_id])

@app.route("/login",methods=['GET', 'POST'])
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
        print ("current user: ", current_user.username)
        return redirect(url_for('index'))
    return render_template('login.html', title='Sign In', form=form)

@app.route("/example", methods=['GET', 'POST'])
def example():
    return render_template("example.html")

@app.route("/example2", methods=['GET', 'POST'])
def example2():
    return render_template("example2.html")

@app.route("/logout",methods=['GET', 'POST'])
def logout():
    remove_player()
    logout_user()
    return redirect(url_for('login'))

@socketio.on('message')
def message(data):
    print ("message received");

@socketio.on("player bet")
def player_bet(bet):
    print ("player bet event received")
    print ("Player bet: " + bet)
    game_id = session.get('game_id')
    if game_id is None:
        print("ERROR: Game not found!!!")
    else:
        nplayer = next_player(current_user.username, players[game_id])
        # If all players have bet, enable next player to play
        game = games[game_id]
        game.place_bet(current_user.username, bet)
        nplayer = game.next_player_to_bet(current_user.username)
        emit("player bet", {'player':current_user.username, 'bet':bet}, room = game_id)
        if nplayer is None:
            emit("player to play", next_player(current_user.username, players[game_id]), room=game_id)
        else:
            emit("player to bet", nplayer, room=game_id)


@socketio.on('player played')
def player_played(data):
    print ("card played event received")
    game_id = session.get('game_id')
    # Emit event to players so they can see the card that was played
    if game_id is None:
        print("ERROR: Game not found!!!")
    else:
        card = data['data']
        new_data = {'player': current_user.username, 'card': card}
        emit("card played", new_data, room=game_id)

        game = games[game_id]
        game.card_played(current_user.username, card)
        cround = games[game_id].get_current_round()
        if cround.last_card_played():
            winner = cround.compute_winner()
            emit("round ended", winner, room=game_id)
            game.create_round()
            nplayer = winner
        else:
            nplayer = next_player(current_user.username, players[game_id])

        emit("player to play", nplayer, room=game_id)


@socketio.on('start hand')
def start_hand(nbcards, trump):
    #selection = data["selection"]
    #votes[selection] += 1
    print ("start hand event received")
    print (nbcards)
    print("Trump:", trump)

    game_id = session.get('game_id')
    if not game_id in games:
        a_game = RomWhistGame();
        games[game_id] = a_game

    a_game = games[game_id]

    hands = a_game.create_hands(int(nbcards), trump)
    round = a_game.create_round()

    # FInd out who the first player to bet is
    nplayer = next_player(current_user.username, players[game_id])

    # Distribute cards to each players
    for player in players[game_id]:
        cards = hands[player].serialize()
        print ("Cards for player ", player, " ", cards)
        emit("new hand", cards, room=clients[game_id][player])

    if trump:
        emit("trump card", str(a_game.trump_card), room=game_id)

    emit("player to bet", nplayer, room=game_id)

# Data should contain the game_id
@socketio.on('join game')
def on_join(data):
    print ("on_join")
    game_id = session['game_id']
    if session['game_id'] in games:
        print("Adding client session to list of clients")
        clients[game_id][current_user.username] = request.sid
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
        emit("game stopped", current_user.username, room=game_id)
        del games[game_id]



# Added a player to a game
def add_player(game_id):
    session['game_id'] = game_id
    players[game_id].append(current_user.username)
    games[game_id].add_player(current_user.username)
    # send(current_user.username + ' has joined game', room=game_id)
    socketio.emit("new player", current_user.username, room=game_id)

def remove_player():
    game_id = session.get('game_id')
    if not game_id is None:
        players[game_id].remove(current_user.username)
        games[game_id].remove_player(current_user.username)
        # send(current_user.username + ' has joined game', room=game_id)
        # leave_room(game_id)
        del clients[game_id][current_user.username]
        socketio.emit("player left", current_user.username, room=game_id)

def next_player(player, list_players):
    pos = list_players.index(player)
    if pos == len(list_players)-1:
        return list_players[0]
    else:
        return list_players[pos+1]
# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
