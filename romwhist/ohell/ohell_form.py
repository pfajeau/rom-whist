from wtforms import BooleanField, IntegerField
from wtforms.validators import InputRequired, NumberRange

from romwhist.forms import StartForm

class OhellStartForm(StartForm):
    multiple_one_card = BooleanField("Multiple one card deals: ", default=False)
    multiple_no_trump = BooleanField("Multiple no trump deals: ", default=True)
    increment = IntegerField("Increment between deals: ", default=1,
                             validators=[InputRequired(), NumberRange(min=1, max=5,
                                                                      message="Enter an increment between 1 and 5")])
