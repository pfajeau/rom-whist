"""
This module implements belote form functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from wtforms import IntegerField
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

from wtforms.validators import InputRequired, NumberRange
from romwhist.forms import StartForm


class BeloteStartForm(StartForm):

    points_to_reach = IntegerField(_l("points_limit"), default=1000,
                                   validators=[InputRequired(), NumberRange(min=50, max=2000,
                                                                            message=_("number_between_500_and_2000"))])
