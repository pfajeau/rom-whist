from wtforms import IntegerField
from wtforms.validators import InputRequired, NumberRange
from romwhist.forms import StartForm


class BeloteStartForm(StartForm):
    points_to_reach = IntegerField("Stop game after player/team reach: ", default=1000,
                                   validators=[InputRequired(), NumberRange(min=50, max=2000,
                                                                            message="Enter a anumber between 500 and 2000")])
