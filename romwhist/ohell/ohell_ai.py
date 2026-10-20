"""
This module implements ohell ai functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import copy
import json
import logging

from romwhist.ai.ai_player import AiPlayer
from romwhist.ohell.ohell_search import WhistSearchAgent
from romwhist.ohell.ohell_state import OhellState
from romwhist.ohell.ohell import OhellGame
from romwhist.ohell.ohell_strategy import WhistTacticalAgent


class OhellAiPlayer(AiPlayer):
    def __init__(self, name, game_id):
        AiPlayer.__init__(self, name, game_id)
        self.__agent = WhistSearchAgent('OhellSim', name, num_simulations=100)
        self.__agent2 = WhistSearchAgent('OhellSim', name, num_simulations=100)
        self.game_state = OhellState(game_id, self.player.name)

    def player_to_bet(self, allowed_bets, game_state_json):
        self.game_state = OhellState(**json.loads(game_state_json))
        if allowed_bets is not None:
            self.game_state.allowed_bets = list(allowed_bets)
        if len(self.game_state.allowed_bets) == 1:
            return int(self.game_state.allowed_bets[0])
        best_bet = self.compute_bet_agent()
        logging.info('Whist AI bid: %s', best_bet)
        return int(best_bet)

    def compute_bet_agent(self):
        return self.__agent2.get_bet(self.game_state)

    def compute_bet_heuristics(self):
        state = copy.deepcopy(self.game_state)
        state.active_player = self.player
        game = OhellGame(state.owner)
        game.populate_from_state(state)
        allowed = [int(bid) for bid in state.allowed_bets]
        return WhistTacticalAgent().estimate_bid(game, self.player, allowed)

    def player_to_play(self, allowed_cards, game_state_json):
        self.game_state = OhellState(**json.loads(game_state_json))
        cards = self.game_state.allowed_cards
        if not cards:
            raise ValueError('No legal card for Whist AI')
        if len(cards) == 1:
            return cards[0]
        return self.__agent.get_action(self.game_state)

    @staticmethod
    def get_game_state_from_json(state_as_json):
        return OhellState(**json.loads(state_as_json))

    def set_game_state_from_json(self, state_as_json):
        self.game_state = self.get_game_state_from_json(state_as_json)
