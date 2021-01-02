from enum import Enum

class Card(object):

    class SuitName(Enum):
        CLUB = "Club"
        DIAMOND = "Diamond"
        HEART = "Heart"
        SPADE = "Spade"

    SUITS = 'cdhs'
    SUIT_NAMES = ["Club", "Diamond", "Heart", "Spade"]

    NUMBERS = list(range(2, 15))
    CARD_NAMES = ['Two', 'Three', 'Four', 'Five', 'Six',
                  'Seven', 'Eight', 'Nine', 'Ten',
                  'Jack', 'Queen', 'King', 'Ace']

    SUIT_NAMES_BY_INITIAL = {
        "c": SuitName.CLUB,
        "d": SuitName.DIAMOND,
        "h": SuitName.HEART,
        "s": SuitName.SPADE
    }

    def __init__(self, card_number, suit):
        self.card_num = card_number
        self.suit_char = suit
        self.rank = self.card_num     # Strength of card
        self.points = 0  # Default    # How many points a card is worth

    @classmethod
    def card_from_value (cls, card_value):
        print ("card_from_value:", card_value)
        print (card_value[1:len(card_value)])
        return cls(int(card_value[1:len(card_value)]), card_value[0])

    def get_suit(self):
        return self.suit_char

    def get_card_num(self):
        return self.card_num

    def get_suit_name(self):
        index = self.SUITS.index(self.suit_char)
        return self.SUIT_NAMES[index]

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
        return self.get_card_name() + ' of ' + self.get_suit_name()
