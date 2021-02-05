import json
import numpy as np


class GameState:

    def __init__(self, game_id, sim_player=None, players=[], trump="", cards_played_per_player=None,
                 cards_played_per_round=dict(), deck_size=0,
                 hand_cards=dict(), allowed_cards=[], active_player="", scores=dict(),
                 owner="", dealer="", bets=dict(), allowed_bets=[], trump_card="", hand_points=dict()):
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
        self.allowed_bets = allowed_bets
        self.sim_player = sim_player
        self.bets = bets
        self.trump_card = trump_card
        self.hand_points = hand_points

        # Can be calculated
        # self.cards_played = []
        # self.cards_played_by_suit = {'c':[], 'd':[], 'h':[], 's':[]}
        # self.hand_cards_as_str = ""

    def get_legal_actions(self):
        return self.allowed_cards

    def get_legal_bets(self):
        return self.allowed_bets

    def toJson(self):
        return json.dumps(self.__dict__)

    def next_player(self, player):
        pos = self.players.index(player)
        if pos == len(self.players) - 1:
            return self.players[0]
        else:
            return self.players[pos + 1]



