# Hand.py
class Hand(object):

    """A labeled collection of cards that can be sorted"""

    def __init__(self, deck, nb_cards=0, label=""):
        self.cards = []
        self.label = label
        for c in range(nb_cards):
            card = deck.deal()
            self.cards.append(card)
            #self._hands[players[p]].sort()


    def add(self, card):
        self.cards.append(card)

    def remove(self, card):
        self.cards.remove(card)

    def sort(self):
        """ Arrange the cards in descending bridge order."""
        self.cards.sort()
        self.cards.reverse()

    def get_cards(self):
        return self.cards

    def serialize(self):
        my_cards=[]
        for card in self.cards:
            my_cards.append(str(card))
        return my_cards

    def dump(self):

        """ Print out contents of the Hand."""

        print(self.label + "'s Cards:")
        for c in self.cards:
            print("   ", c)
