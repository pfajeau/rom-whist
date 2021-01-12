from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, IntegerField, SelectField
from wtforms.validators import Length, InputRequired, ValidationError, Regexp, NumberRange
from romwhist.forms import StartForm

class BeloteStartForm(StartForm):
    points_to_reach = IntegerField("Stop game after player/team reach: ", default=1000,\
                                    validators=[InputRequired(), NumberRange(min=500, max=2000, \
                                    message="Enter a anumber between 500 and 2000")])
