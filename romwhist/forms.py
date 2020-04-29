"""
This module implements webapp forms.

author: Philippe Fajeau
"""

# TODO - create your forms here

# Optionally import flask-wtf and wtforms
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField
from wtforms.validators import Length, InputRequired, ValidationError

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(max=32)])
#    password = PasswordField("Password", validators=[InputRequired(), Length(min=1, max=32)])
    submit = SubmitField('Sign In')
    remember_me = BooleanField('Remember Me')

class StartGameForm(FlaskForm):
    game_id = StringField("Game id: ", validators=[InputRequired(), Length(max=32)])
    start_game = SubmitField('Submit')

class JoinGameForm(FlaskForm):
    game_id = StringField("Game id: ", validators=[InputRequired(), Length(max=32)])
    join_game = SubmitField('Join game')

class GameForm(FlaskForm):
    nb_cards = IntegerField("Nb Cards: ", validators=[InputRequired(), Length(max=2)])
    trump = BooleanField("Trump: ", validators=[InputRequired()], default=True)
    leave_game = SubmitField('Leave game')
    stop_game = SubmitField('Stop game')
    restart_game = SubmitField('Restart game')
    #user_name = HiddenField("user_name")

class IndexForm(FlaskForm):
    game_id = StringField("Game id: ", validators=[Length(max=6)])
    user_name = StringField("Your Alias: ", validators=[InputRequired(), Length(max=10)])
    start_game = SubmitField('Start a new game')
    join_game = SubmitField('Join an existing game')

from .models import *
