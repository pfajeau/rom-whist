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
from .forms import LoginForm, StartGameForm, JoinGameForm, GameForm
from flask_login import current_user, login_user, logout_user
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
hands = dict()

@app.route("/")
@app.route("/index")
def index():
    # TODO - add here endpoint of resource where you want to land on page load. e.g.
    # return redirect(url_for("auth_blueprint.home"))
    return render_template("index.html")

@app.route("/base")
def base():
    # TODO - add here endpoint of resource where you want to land on page load. e.g.
    # return redirect(url_for("auth_blueprint.home"))
    return render_template("base.html")

@app.route("/startgame",methods=['GET', 'POST'])
def get_game_id():
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
        return redirect(url_for('login'))
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

    hands[game_id] = a_game.create_hands(int(nbcards), trump)
    # hands[game_id] = a_game.create_hands(int(nbcards), trump_flag)
    round = a_game.create_round()
    hands[game_id] = a_game.get_hands()

    # Distribute cards to each players
    for player in players[game_id]:
        cards = hands[game_id][player].serialize()
        print ("Cards for player ", player, " ", cards)
        emit("new hand", cards, room=clients[game_id][player])

    if trump:
        emit("trump card", str(a_game.trump_card), room=game_id)

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

# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
