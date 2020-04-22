from .card import Card
# from .deck import Deck
# from random import choice
# from random import randrange
from .hand import Hand

class Round():

    def __init__(self, players, nb_cards, deck, with_trump=False):
        self.trump_card = None
        self.players = players
        self._hands = dict()

        for p in range(len(self.players)):
            hand = Hand(players[p])
            self._hands[players[p]] = hand
            for c in range(nb_cards):
                card = deck.deal()
                hand.add(card)
            #TODO
            #self._hands[players[p]].sort()
        # Pick up trum cards
        if with_trump:
            self.trump_card = deck.deal()

        # The cards played during the round
        self.cards_played = dict()
        self.winning_player = ""

    def hands(self):
        return self._hands

    def trump(self):
        return self.trump_card

    # Return the number of players left to play for the Round
    # when last player has played, return 0
    def card_played(self, player, card_str):
        if not self.cards_played:
            # First card played
            self.first_player = player
        card = Card.card_from_value(card_str)
        print (card_str, " ", card)
        self.cards_played[player] = card
        self._hands[player].remove(card)
        return len (self.players) - len(self.cards_played)

    def last_card_played(self):
        return len(self.cards_played) == len (self.players)

    # Override for a particular game
    def compute_winner(self):
        self.winning_player = self.winning_player_for_suit(self.cards_played[self.first_player].suit)

        # If there is a trump, highest trump card wins
        if not self.trump_card is None:
            self.winning_player = self.winning_player_for_suit(self.trump_card.suit())
        return self.winning_player

    def winning_player_for_suit (self, a_suit):
        self.winning_player = self.first_player
        for player in self.cards_played:
            if self.cards_played[player].suit == a_suit and \
            self.cards_played[player].rank() > self.cards_played[self.winning_player].rank():
                self.winning_player = player
        return self.winning_player
