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
    nb_cards = IntegerField("Number of cards: ", validators=[InputRequired(), Length(max=2)])
    trump = BooleanField("With Trump: ", validators=[InputRequired()])
    #user_name = HiddenField("user_name")

class IndexForm(FlaskForm):
    user_name = StringField("User Name: ", validators=[InputRequired(), Length(max=10)])
    start_game = SubmitField('Start a new game')
    join_game = SubmitField('Join an existing game')

from .models import *
