from romwhist.card import Card
# from .deck import Deck
# from random import choice
# from random import randrange
from romwhist.hand import Hand

class Round():

    def __init__(self, players, trump_suit):
        self.trump_suit = trump_suit
        self.players = players

        # The cards played during the round
        self.cards_played = dict()
        self.winning_player = ""
        self.first_card_played=None
        self.round_started = False

    # Return the number of players left to play for the Round
    # when last player has played, return 0
    def card_played(self, player, card):
        if not self.round_started:
            # First card played
            self.first_player = player
            self.first_card_played = card
            self.round_started = True

        self.cards_played[player] = card
        return len (self.players) - len(self.cards_played)

    def get_first_card_played(self):
        return self.first_card_played;

    # REturn a list of cards as strings
    def get_cards_played(self):
        cards = list(self.cards_played.values())
        str_cards = []
        for card in cards:
            str_cards.append(str(card))
        return str_cards

    def last_card_played(self):
        return len(self.cards_played) == len (self.players)

    # Override for a particular game
    def compute_winner(self):
        self.winning_player = self.winning_player_for_suit(self.cards_played[self.first_player].get_suit)

        # If there is a trump, highest trump card wins
        if not self.trump_suit is None:
            self.winning_player = self.winning_player_for_suit(self.trump_suit)
        return self.winning_player

    def winning_player_for_suit (self, trump_suit):
        self.winning_player = self.first_player
        winning_suit = self.cards_played[self.first_player].get_suit()
        trump_played = False
        for player in self.cards_played:
            print ("player - suit - rank: ", player, self.cards_played[player].get_suit(), self.cards_played[player].get_card_num())
            if self.cards_played[player].get_suit() == trump_suit and not trump_played:
                trump_played = True
                winning_suit = trump_suit
                self.winning_player = player
            else:
                if self.cards_played[player].get_suit() == winning_suit and \
                self.cards_played[player] > self.cards_played[self.winning_player]:
                    self.winning_player = player

        return self.winning_player
