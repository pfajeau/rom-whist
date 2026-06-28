"""
This module implements poker form functionality.
"""

from flask_babel import lazy_gettext as _l
from wtforms import IntegerField, SelectField
from wtforms.validators import InputRequired, NumberRange

from romwhist.forms import StartForm


class PokerStartForm(StartForm):
    poker_type = SelectField(
        _l("poker_type"),
        choices=[
            ("texas_holdem", _l("Texas Hold'em")),
            ("omaha", _l("Omaha")),
        ],
        default="texas_holdem",
        validators=[InputRequired()],
    )
    initial_money = IntegerField(
        _l("initial_money"),
        default=1000,
        validators=[InputRequired(), NumberRange(min=10, max=10000)],
    )