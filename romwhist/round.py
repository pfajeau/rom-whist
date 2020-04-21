# from .card import Card
# from .deck import Deck
# from random import choice
# from random import randrange
from .hand import Hand

class Round():

    def __init__(self, players, nb_cards, deck, trump=None):
        self.players = players
        self._hands = dict()
        for p in range(len(self.players)):
            hand = Hand(players[p])
            self._hands[players[p]] = hand
            for c in range(nb_cards):
                card = deck.deal()
                hand.add(card)

        # The cards played during the round
        cards_played = dict()
        # Trump color, can be "s", "c", "h", or "d"
        self.trump = trump
        self.winning_player = ""

    def hands(self):
        return self._hands

    # Return the number of players left to play for the Round
    # when last player has played, return 0
    def card_played(self, player, card):
        if not self.cards_played:
            # First card played
            self.first_player = player
        self.cards_played[player] = card
        self._hands[player].remove(card)
        return len (self.players) - len(self.cards_played)

    def last_card_played(self):
        return len(self.cards_played) == len (self.players)

    # Override for a particular game
    def compute_winner(self):
        winning_player = winning_player_for_suit(cards_played[self.first_player].suit)

        # If there is a trump, highest trump card wins
        if not trump is None:
            winning_player = winning_player_for_suit(trump)

    def winning_player_for_suit (a_suit):
        winning_player = self.first_player
        for player in self.card_played:
            if self.cards_played[player].suit == a_suit and \
            self.cards_played[player].rank > self.cards_played[winning_player].rank:
                winning_player = player
        return winning_player
