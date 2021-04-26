from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

from wtforms import SelectField
from romwhist.belote.belote_form import BeloteStartForm
from romwhist.contree.contree import CountingMethod


class ContreeStartForm(BeloteStartForm):

    counting = SelectField(_l(u"counting"),
                           choices=[(0, CountingMethod.POINTS_BID.value),
                                    (1, CountingMethod.POINTS_ACHIEVED.value),
                                    (2, CountingMethod.POINTS_ACHIEVED_PLUS_BID.value)],
                           default= CountingMethod.POINTS_BID.value)
