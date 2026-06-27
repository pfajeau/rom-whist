"""
This module implements poker form functionality.
"""

from flask_babel import lazy_gettext as _l
from wtforms import SelectField
from wtforms.validators import InputRequired

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