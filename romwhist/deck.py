"""
This module implements deck functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import logging
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
        self.all_cards = cards.copy()
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

    def add_top(self, card):
        if card is None:
            return
        else:
            self.cards.append(card)
            self._size += 1
            return

    def add_random(self, card):
        if card is None:
            return
        else:
            place = random.randint(0,self._size) # getting a random position for the card to be place into
            self.cards.insert(place,card) # putting the card into place position in the deck
            self._size += 1 # incrementing the size of the deck
            return

    def add_bottom(self, card):
        if card is None:
            return
        else:
            self.cards.insert(0,card) # put the card to the bottom of the deck
            self._size += 1 # increment size of the deck
            return

    def remove_card(self, card):
        if card in self.cards:
            self.cards.remove(card)
        else:
            logging.warning("Asked to remove card that does not exist in deck: %s", str(card))