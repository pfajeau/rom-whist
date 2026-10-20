"""
This module implements belote ai functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import json
import logging

from romwhist.belote.belote_search import BeloteSearchAgent
from romwhist.ai.ai_player import AiPlayer
from romwhist.belote.belote_state import BeloteState


# TODO: factorize with OhellAIPlayer
class BeloteAiPlayer(AiPlayer):

    def __init__(self, player, id):
        AiPlayer.__init__(self, player, id)
        self._agent = BeloteSearchAgent('BeloteSim', self.player, num_simulations=100)
        self._agent2 = BeloteSearchAgent('BeloteSim', self.player, num_simulations=100)
        self.game_state = BeloteState(id, self)

    def player_to_play(self, allowed_cards, game_state_json):
        game_state = BeloteState(**json.loads(game_state_json))
        return self.player_to_play_from_state(game_state)

    def player_to_play_from_state(self, game_state):
        self.game_state = game_state

        # If only one action possible return it right away
        if len(self.game_state.allowed_cards) == 1:
            logging.debug("Only one card allowed: %s", self.game_state.allowed_cards[0] )
            return self.game_state.allowed_cards[0]

        if len(self.game_state.allowed_cards) == 0:
            raise RuntimeError("Allowed cards is empty!")

        best_card = self._agent.get_action(self.game_state)
        logging.info("Agent calculated card: %s", best_card)
        return best_card

    @staticmethod
    def get_game_state_from_json(state_as_json):
        state = BeloteState(**json.loads(state_as_json))
        return state

    def set_game_state_from_json(self, state_as_json):
        self.game_state = self.get_game_state_from_json(state_as_json)

    def player_to_bet(self, allowed_bets, game_state_json):
        logging.debug("Belote AI PLayer to bet: %s", self.player.name)
        logging.debug("Game state: %s", game_state_json)
        game_state = BeloteState(**json.loads(game_state_json))
        self.game_state = game_state

        # Make active player the one that will start playing
        # for the simulated game
        self.game_state.active_player = self.game_state.next_player(self.game_state.dealer)

        bet = self._agent2.get_bet(self.game_state)

        if bet is None:
            return "pass"

        # The search applies the configurable bidding risk threshold. Card
        # selection has no such cutoff: an AI must play even in a losing hand.
        return bet

    def compute_bet_agent(self):
        return self._agent2.get_bet(self.game_state)


