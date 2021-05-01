# from .deck import Deck
# from random import choice
# from random import randrange

class Round:

    def __init__(self, players, trump_suit):
        self.trump_suit = trump_suit
        self.players = players

        # The cards played during the round
        self.cards_played = dict()
        for player in players:
            self.cards_played[player] = None
        self.winning_player = ""
        self.first_card_played=None
        self.round_started = False
        self.winning_card = None

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
        return self.first_card_played

    # REturn a list of cards as strings
    def get_cards_played(self):
        cards = list(self.cards_played.values())
        str_cards = []
        for card in cards:
            str_cards.append(card)
        return str_cards

    def last_card_played(self):
        for player in self.players:
            if self.cards_played[player] is None:
                return False
        return True

    # Override for a particular game
    def compute_winner(self):
        self.winning_player = self.winning_player_for_suit(self.cards_played[self.first_player].get_suit_name())

        # If there is a trump, highest trump card wins
        if not self.trump_suit is None:
            self.winning_player = self.winning_player_for_suit(self.trump_suit)

        return self.winning_player

    def winning_player_for_suit (self, suit):
        #print ("Suit passed to winning_player_for_suit : " + suit)
        self.winning_player = self.first_player
        winning_suit = self.cards_played[self.first_player].get_suit_name()
        #print ("Winning suit: " + winning_suit)
        trump_played = False
        for player in self.cards_played:
            if not self.cards_played.get(player) is None:
                # print ("player - suit - rank: ", player, self.cards_played[player].get_suit(), self.cards_played[player].rank)
                if self.cards_played[player].get_suit_name() == self.trump_suit and not trump_played:
                    trump_played = True
                    winning_suit = self.trump_suit
                    self.winning_player = player
                else:
                    if self.cards_played[player].get_suit_name() == winning_suit and \
                    self.cards_played[player] > self.cards_played[self.winning_player]:
                        self.winning_player = player

        return self.winning_player
