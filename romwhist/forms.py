"""
This module implements webapp forms.

author: Philippe Fajeau
"""

# TODO - create your forms here

# Optionally import flask-wtf and wtforms
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import Length, InputRequired, ValidationError

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(max=32)])
#    password = PasswordField("Password", validators=[InputRequired(), Length(min=1, max=32)])
    submit = SubmitField('Sign In')
    remember_me = BooleanField('Remember Me')
from .models import *
