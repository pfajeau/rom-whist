"""
This module implements webapp forms.

author: Philippe Fajeau
"""

# TODO - create your forms here

# Optionally import flask-wtf and wtforms
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField
from wtforms.validators import Length, InputRequired, ValidationError, Regexp

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
    #user_name = HiddenField("user_name")

class IndexForm(FlaskForm):
    game_id = StringField("Game id: ", validators=[Length(max=6)])
    user_name = StringField("Your Alias: ", validators=[InputRequired(), Length(max=10), Regexp("^[a-zA-Z0-9]+$")])
    start_game = SubmitField('Create new game')
    join_game = SubmitField('Join existing game')
    deck_size = SelectField("Deck size: ", choices=[('32','32'),('52','52')], default='52')
    multiple_one_card = BooleanField("Multiple one card deals: ", default=False)
    multiple_no_trump = BooleanField("Multiple no trump deals: ", default=True)
    increment = IntegerField("Increment: ", default=1)

from .models import *
