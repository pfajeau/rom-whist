"""
This module implements ohell form functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from flask_babel import lazy_gettext as _l
from flask_babel import gettext as _
from wtforms import BooleanField, IntegerField
from wtforms.validators import InputRequired, NumberRange

from romwhist.forms import StartForm


class OhellStartForm(StartForm):
    multiple_one_card = BooleanField(_l(u"multiple_one_card_deals"),
                                     default=False)
    multiple_no_trump = BooleanField(_l(u"multiple_no_trump_deals"),
                                     default=True)
    increment = IntegerField(_l(u"increment_between_deals"), default=1,
                             validators=[InputRequired(),
                                         NumberRange(min=1, max=5,
                                                     message=_l("enter_increment_between_1_and_5"))])

