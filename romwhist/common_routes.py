"""
This module implements common code betwenn routes.

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
from romwhist import socketio,app
from romwhist.forms import LoginForm, StartForm, GameForm
from romwhist.models import User
from romwhist.extensions import db

#def stats():

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


def post_msg(msg, sender, room, namespace):
    game_id = session.get('game_id')
    if game_id is None:
        print("NO GAME_ID IN SESSION!!!!")
    else:
        socketio.emit("msg posted", {'sender': sender, 'msg': msg}, room=room, namespace=namespace)

def restart_hand(game, namespace):
    # Deal another hand
    socketio.emit("alert", "Hand to be replayed", room=game.id, namespace=namespace)
    if game.started:
      game._current_hand_nb = game._current_hand_nb - 1  # Deal again
      generate_hands(game.id, game.dealer)

def add_player(user, game, namespace):
    game.add_player(user)
    socketio.emit("new player", user, room=game.id, namespace=namespace)
    if game.started:
        restart_hand(game, namespace)


