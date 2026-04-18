"""
This module implements forms functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""


from flask_babel import lazy_gettext as _l

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField
from wtforms.validators import Length, InputRequired, Regexp, NumberRange


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[InputRequired(), Length(max=32)])
#    password = PasswordField("Password", validators=[InputRequired(), Length(min=1, max=32)])
    submit = SubmitField('Sign In')
    remember_me = BooleanField('Remember Me')


class GameForm(FlaskForm):
    #user_name = HiddenField("user_name")
    i=1  # dummy, need a form for hidden field


class StartForm(FlaskForm):
    game_id = StringField(_l(u"game_id"), validators=[Length(max=6)])
    user_name = StringField(_l(u"alias"), validators=[InputRequired(), Length(max=10), Regexp("^[a-zA-Z0-9]+$", message="Only alphanumeric characters are allowed for alias")])
    start_game = SubmitField(_l(u'create_new_game'))
    join_game = SubmitField(_l(u'join_game'))
    #deck_size = SelectField("Deck size: ", choices=[('24','24'),('32','32'),('40','40'),('52','52')], default='32')

