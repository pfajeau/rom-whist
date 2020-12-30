import random
from romwhist.card import Card

class Deck(object):

    def __init__(self, deck_size=52):

        cards = []
        nb_ranks = int(deck_size / 4)
        remainder = deck_size % 4
        for suit in Card.SUITS:
            ranks = Card.NUMBERS[len(Card.NUMBERS) - nb_ranks: len(Card.NUMBERS)]
            for rank in ranks:
                cards.append(Card(rank,suit))

        # TODO: should add extra cards to account for remainder
        # Only applies when size is not a multiple of 4
        self.cards = cards # cards in the deck
        self._size = deck_size # number of cards initally in a deck

    def size(self):
        return self._size

    def deal(self):
        # Deal a single card, Returns the next card in self, and removes it from self
        if self._size > 0:
            card = self.cards.pop()
            self._size -= 1
            return card
        else:
            return None

    def shuffle(self):
        random.shuffle(self.cards)

    def addTop(self,card):
        self.cards.append(card)
        self._size += 1

    def addRandom(self,card):
        place = random.randint(0,self._size) # getting a random position for the card to be place into
        self.cards.insert(place,card) # putting the card into place position in the deck
        self._size += 1 # incrementing the size of the deck

    def addBottom(self,card):
        self.cards.insert(0,card) # put the card to the bottom of the deck
        self._size += 1 # increment size of the deck
