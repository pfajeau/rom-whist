# Card.py
class Card(object):
    '''A simple playing card. A Card is characterized by two components:
    rank: an integer value in the range 1-13, inclusive (Ace-King)
    suit: a character in 'cdhs' for clubs, diamonds, hearts, and
    spades.'''

    SUITS = 'cdhs'
    SUIT_NAMES = ['Clubs', 'Diamonds', 'Hearts', 'Spades']

    RANKS = list(range(2,14))
    RANK_NAMES = ['Two', 'Three', 'Four', 'Five', 'Six',
                  'Seven', 'Eight', 'Nine', 'Ten',
                  'Jack', 'Queen', 'King', 'Ace']

    def __init__(self, rank, suit):
        self.rank_num = rank
        self.suit_char = suit

    @classmethod
    def card_from_value (cls, card_value):
        print ("card_from_value:", card_value)
        print (card_value[1:len(card_value)])
        return cls(int(card_value[1:len(card_value)]), card_value[0])

    def suit(self):
        return self.suit_char

    def rank(self):
        return self.rank_num

    def suitName(self):
        index = self.SUITS.index(self.suit_char)
        return self.SUIT_NAMES[index]

    def rankName(self):
        index = self.RANKS.index(self.rank_num)
        return self.RANK_NAMES[index]

    def __eq__(self, other):
        return str(self) == str(other)

    def __str__(self):
        '''String representation
        post: Returns string representing self, e.g. 'Ace of Spades' '''

        return str(self.suit_char) + str(self.rank_num)
        #return self.rankName() + ' of ' + self.suitName()
