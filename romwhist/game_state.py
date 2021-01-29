from abc import ABC, abstractmethod

import logging

from romwhist.card import Card

class GameState(ABC):

    def __init__(self, game_id, sim_player, players=[], trump="", cards_played_per_player=None,
                 cards_played_per_round=None, deck_size=0,
                 hand_cards=None, allowed_cards=[], active_player=""):
        self.game_id = game_id
        self.players = players
        self.trump = trump
        self.cards_played_per_player = cards_played_per_player
        #self.cards_played_per_round = cards_played_per_round
        self.deck_size = deck_size
        self.hand_cards = hand_cards
        self.allowed_cards = allowed_cards
        self.active_player = active_player
        self.cards_played_per_round = cards_played_per_round

        self.sim_player = sim_player
        self.deck = None

        # Can be calculated
        self.cards_played = []
        self.cards_played_by_suit = {'c':[], 'd':[], 'h':[], 's':[]}
        self.hand_cards_as_str = ""

    def get_legal_actions(self):
        return self.allowed_cards

