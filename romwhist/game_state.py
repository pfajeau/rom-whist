from abc import ABC, abstractmethod
import json
import logging

from romwhist.card import Card

class GameState(ABC):

    def __init__(self, game_id, sim_player=None, players=[], trump="", cards_played_per_player=None,
                 cards_played_per_round=dict(), deck_size=0,
                 hand_cards=dict(), allowed_cards=[], active_player="", scores=dict(),
                 owner="", dealer=""):
        self.game_id = game_id
        self.players = players
        self.trump = trump
        self.cards_played_per_player = cards_played_per_player
        self.deck_size = deck_size
        self.hand_cards = hand_cards
        self.allowed_cards = allowed_cards
        self.active_player = active_player
        self.cards_played_per_round = cards_played_per_round
        self.scores = scores
        self.owner = owner
        self.dealer = dealer

        self.sim_player = sim_player

        # Can be calculated
        # self.cards_played = []
        # self.cards_played_by_suit = {'c':[], 'd':[], 'h':[], 's':[]}
        # self.hand_cards_as_str = ""

    def get_legal_actions(self):
        return self.allowed_cards

    def toJson(self):
        return json.dumps(self.__dict__)

