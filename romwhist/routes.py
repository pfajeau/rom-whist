"""
This module implements routes.

author: Philippe Fajeau

"""
from flask import Blueprint
from . import controllers
from romwhist import socketio,app
from flask import render_template, request, flash, session, url_for, redirect
from .forms import LoginForm, StartGameForm, JoinGameForm
from flask_login import current_user, login_user
from romwhist.models import User
from romwhist.extensions import db
from flask_socketio import join_room, leave_room
from flask_socketio import SocketIO, emit

# Map of games, key is game id
games = dict()

# Map keyed by game ids and containing list of players for each game id
players = dict()

print (socketio)




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
def start_game():
    print("Current User: ", current_user.username)
    if current_user.is_authenticated:
        form = StartGameForm()
        if form.validate_on_submit():
            game_id = form.game_id.data
            print("creating new game with id: ", game_id)
            # Add game id in session
            session['game_id'] = game_id
            players[game_id] = [current_user.username]
            return render_template('game.html', title='Bla', form=form)
        else:
            return render_template('start_game.html', title='Bla', form=form)
    else:
        form = LoginForm()
        return render_template('login.html', title='Sign In', form=form)

@app.route("/joingame",methods=['GET', 'POST'])
def join_game():
    print("Current User: ", current_user.username)
    if current_user.is_authenticated:
        form = JoinGameForm()
        if form.validate_on_submit():
            game_id = form.game_id.data
            print("game id: ", game_id)
            # Add player to session. TODO: should check whehter user is already in list
            if game_id in players:
                players[game_id].append(current_user.username)
                join_room(game_id)
                send(current_user.username + ' has joined game', room=game_id)
                return render_template('game.html', title='Bla', form=form)
            else:
                form = StartGameForm()
                return render_template('start_game.html', title='Bla', form=form)
        else:
            return render_template('join_game.html', title='Bla', form=form)
    else:
        form = LoginForm()
        return render_template('login.html', title='Sign In', form=form)

@app.route("/game")
def play():
    return render_template("game.html")

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

@socketio.on('message')
def message(data):
    print ("message received");

@socketio.on('get card')
def get_card(data):
    #selection = data["selection"]
    #votes[selection] += 1
    print ("get card event received")
    card = "Ace of Spades"
    emit("new card", card, broadcast=True)

@socketio.on('join')
def on_join(data):
    username = data['username']
    room = data['room']
    join_room(room)
    send(username + ' has entered the room.', room=room)

@socketio.on('leave')
def on_leave(data):
    username = data['username']
    room = data['room']
    leave_room(room)
    send(username + ' has left the room.', room=room)
# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
