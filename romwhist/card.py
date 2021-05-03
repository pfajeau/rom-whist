from flask_babel import gettext as _
from flask_babel import lazy_gettext as _l

class Card(object):

    SUITS = 'cdhs'

    SUIT_NAMES = ["club", "diamond", "heart", "spade"]

    NUMBERS = list(range(2, 15))
    CARD_NAMES = ['two', 'three', 'four', 'five',
                  'six', 'seven', 'eight', 'nine',
                  'ten', 'jack', 'queen', 'king', 'ace']

    SUIT_NAMES_BY_INITIAL = {
        'c': "club",
        'd': "diamond",
        'h': "heart",
        's': "spade"}
    

    def __init__(self, card_number, suit):
        self.card_num = card_number
        self.suit_char = suit
        self.rank = self.card_num     # Strength of card
        self.points = 0  # Default    # How many points a card is worth

    @classmethod
    def card_from_value (cls, card_value):
        if card_value == 'None':
            return None
        else:
            return cls(int(card_value[1:len(card_value)]), card_value[0])

    @classmethod
    def get_suit_initial (cls, suit_name):
        index = list(Card.SUIT_NAMES_BY_INITIAL.values()).index(suit_name)
        return list(Card.SUIT_NAMES_BY_INITIAL.keys())[index]

    def get_suit(self):
        return self.suit_char

    def get_card_num(self):
        return self.card_num

    def get_suit_name(self):
        # index = self.SUITS.index(self.suit_char)
        # return self.SUIT_NAMES[index]
        return Card.SUIT_NAMES_BY_INITIAL[self.suit_char]

    def get_card_name(self):
        index = self.NUMBERS.index(self.card_num)
        return self.CARD_NAMES[index]

    def __lt__(self, other):
        return self.rank < other.rank

    def __gt__(self, other):
        return self.rank > other.rank

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        return str(self.suit_char) + str(self.card_num)
        #return self.rankName() + ' of ' + self.suitName()

    def desc(self):
        return _l(self.get_card_name()) + " " + _('of') + \
                  " " + _l(self.get_suit_name())
