"""
This module implements routes.

author: Philippe Fajeau

"""
from flask import Blueprint
from . import controllers
from romwhist import app
from flask import render_template, request, flash, session, url_for, redirect
from .forms import LoginForm, StartGameForm
from flask_login import current_user, login_user
from romwhist.models import User
from romwhist.extensions import db

# Map of games, key is game id
games = dict()

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

@app.route("/phil")
def test():
    return render_template("index.html")

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
            players = []
            players.append(currentuser.username)
            session['players'] = players
            return render_template('game.html', title='Bla', form=form)
        else:
            return render_template('start_game.html', title='Bla', form=form)
    else:
        form = LoginForm()
        return render_template('login.html', title='Sign In', form=form)

@app.route("/joingame",methods=['GET', 'POST'])
def start_game():
    print("Current User: ", current_user.username)
    if current_user.is_authenticated:
        form = JoinGameForm()
        if form.validate_on_submit():
            game_id = form.game_id.data
            print("game id: ", game_id)
            # Add player to session. TODO: should check whehter user is already in list
            session['players'].append(current_user)
            return render_template('game.html', title='Bla', form=form)
        else:
            return render_template('start_game.html', title='Bla', form=form)
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


# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
