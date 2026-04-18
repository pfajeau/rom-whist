"""
This module implements contree form functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from flask_babel import lazy_gettext as _l
from flask_babel import gettext as _
from wtforms.validators import InputRequired

from wtforms import SelectField
from romwhist.belote.belote_form import BeloteStartForm
from romwhist.contree.contree import CountingMethod


class ContreeStartForm(BeloteStartForm):

    # TODO: translation of select options are not translated for some reason
    counting = SelectField(
        _("counting"),
        choices=[(CountingMethod.POINTS_BID.value, _l(CountingMethod.POINTS_BID.value)),
                 (CountingMethod.POINTS_ACHIEVED.value, _l(CountingMethod.POINTS_ACHIEVED.value)),
                 (CountingMethod.POINTS_ACHIEVED_PLUS_BID.value, _l(CountingMethod.POINTS_ACHIEVED_PLUS_BID.value))],
        default= CountingMethod.POINTS_BID.value,
        validators=[InputRequired()])

