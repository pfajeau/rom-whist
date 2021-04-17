from enum import Enum

from wtforms import IntegerField, SelectField
from wtforms.validators import InputRequired, NumberRange
from romwhist.belote.belote_form import BeloteStartForm
from romwhist.contree.contree import CountingMethod

class ContreeStartForm(BeloteStartForm):

    counting = SelectField("Counting",
                           choices=[(0, CountingMethod.POINTS_BID.value),
                                    (1, CountingMethod.POINTS_ACHIEVED.value),
                                    (2, CountingMethod.POINTS_ACHIEVED_PLUS_BID.value)],
                           default='Points_Bid')
