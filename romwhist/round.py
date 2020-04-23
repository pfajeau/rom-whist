from .card import Card
# from .deck import Deck
# from random import choice
# from random import randrange
from .hand import Hand

class Round():

    def __init__(self, players, trump_suit):
        self.trump_suit = trump_suit
        self.players = players

        # The cards played during the round
        self.cards_played = dict()
        self.winning_player = ""

    # Return the number of players left to play for the Round
    # when last player has played, return 0
    def card_played(self, player, card):
        if not self.cards_played:
            # First card played
            self.first_player = player
        self.cards_played[player] = card
        return len (self.players) - len(self.cards_played)

    def last_card_played(self):
        return len(self.cards_played) == len (self.players)

    # Override for a particular game
    def compute_winner(self):
        self.winning_player = self.winning_player_for_suit(self.cards_played[self.first_player].suit)

        # If there is a trump, highest trump card wins
        if not self.trump_suit is None:
            self.winning_player = self.winning_player_for_suit(self.trump_suit)
        return self.winning_player

    def winning_player_for_suit (self, a_suit):
        self.winning_player = self.first_player
        for player in self.cards_played:
            print ("player - suit - rank: ", player, self.cards_played[player].suit(), self.cards_played[player].rank())
            if self.cards_played[player].suit() == a_suit() and \
            self.cards_played[player].rank() > self.cards_played[self.winning_player].rank():
                self.winning_player = player
        return self.winning_player
