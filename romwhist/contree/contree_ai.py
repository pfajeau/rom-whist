"""
This module implements contree ai functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import json
import logging
from romwhist.contree.announce import Announce
from romwhist.contree.contree_state import ContreeState
from romwhist.belote.belote_ai import BeloteAiPlayer
from romwhist.belote.belote_search import BeloteSearchAgent
from romwhist.ai.ai_player import AiPlayer


# TODO: factorize with OhellAIPlayer
class ContreeAiPlayer(BeloteAiPlayer):

    def __init__(self, player, game_id):
        AiPlayer.__init__(self, player, game_id)
        self._agent = BeloteSearchAgent('ContreeSim', self.player, num_simulations=15)
        self._agent2 = BeloteSearchAgent('ContreeSim', self.player, num_simulations=15)

        self.game_state = ContreeState(game_id, self)

    def player_to_play(self, allowed_cards, game_state_json):
        game_state = ContreeState(**json.loads(game_state_json))
        return BeloteAiPlayer.player_to_play_from_state(self, game_state)

    @staticmethod
    def get_game_state_from_json(state_as_json):
        state = ContreeState(**json.loads(state_as_json))
        return state

    def set_game_state_from_json(self, state_as_json):
        self.game_state = self.get_game_state_from_json(state_as_json)

    def player_to_bet(self, allowed_bets, game_state_json):
        self.game_state = ContreeState(**json.loads(game_state_json))
        if allowed_bets is not None:
            self.game_state.allowed_bets = allowed_bets
        if self.game_state.get_legal_bets() == ['pass_0']:
            return Announce('pass', 0)
        action = self._agent2.get_bet(self.game_state)
        # Return the actual evaluated contract, including proper zero-point
        # contre/surcontre actions. Never manufacture a bid from an average.
        if action not in self.game_state.get_legal_bets():
            action = 'pass_0'
        bet = Announce.from_str(action)
        logging.info("Agent calculated bet: %s", bet)
        return bet

    def compute_bet_agent(self):
        return self._agent2.get_bet(self.game_state)


