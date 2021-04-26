from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

from wtforms import SelectField
from romwhist.belote.belote_form import BeloteStartForm
from romwhist.contree.contree import CountingMethod


class ContreeStartForm(BeloteStartForm):

    counting = SelectField(_l(u"counting"),
                           choices=[(CountingMethod.POINTS_BID.value, _l(CountingMethod.POINTS_BID.value)),
                                    (CountingMethod.POINTS_BID.value, _l(CountingMethod.POINTS_ACHIEVED.value)),
                                    (CountingMethod.POINTS_ACHIEVED_PLUS_BID.value, _l(CountingMethod.POINTS_ACHIEVED_PLUS_BID.value))],
                           default= CountingMethod.POINTS_BID.value)
