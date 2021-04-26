from wtforms import IntegerField
from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

from wtforms.validators import InputRequired, NumberRange
from romwhist.forms import StartForm


class BeloteStartForm(StartForm):
    points_to_reach = IntegerField(_l(u"points_limit"), default=1000,
                                   validators=[InputRequired(), NumberRange(min=50, max=2000,
                                                                            message=_("number_between_500_and_2000"))])
