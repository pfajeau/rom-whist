from romwhist.card import Card
class Hand(object):

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
        # Sort by color, then by rank
        string_hand=self.serialize()
        res=dict()
        sorted_cards = []
        for suit in 'cdsh':
            res[suit] = []
            for card in self.cards:
                if card.get_suit() == suit:
                    res[suit].append(card)
            res[suit].sort()
            if not res[suit] is None:
                sorted_cards.extend(res[suit])

        self.cards = sorted_cards
        return self

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
