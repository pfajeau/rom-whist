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
from romwhist.belote.belote import BeloteGame
from romwhist.contree.announce import Announce
from romwhist.contree.contree_state import ContreeState
from romwhist.belote.belote_ai import BeloteAiPlayer
from romwhist.ai.ai_agents import SimpleMCTSAgent
from romwhist.ai.ai_player import AiPlayer


# TODO: factorize with OhellAIPlayer
class ContreeAiPlayer(BeloteAiPlayer):

    CORRECTION_FACTOR = 0.9    # Because simulations are optimistic in outcome

    def __init__(self, player, game_id):
        AiPlayer.__init__(self, player, game_id)
        self._agent = SimpleMCTSAgent('ContreeSim', self.player,
                                      action_chooser_function='random_action',
                                      num_simulations=15)

        self._agent2 = SimpleMCTSAgent('ContreeSim', self.player,
                                       action_chooser_function='random_action',
                                       num_simulations=15)

        self.game_state = ContreeState(game_id, self)

        #BeloteAiPlayer.__init__(self, name, game_id)

    def player_to_play(self, allowed_cards, game_state_json):
        game_state = ContreeState(**json.loads(game_state_json))
        return BeloteAiPlayer.player_to_play_from_state(self, game_state)

    @staticmethod
    def get_game_state_from_json(state_as_json):
        state = ContreeState(**json.loads(state_as_json))
        return state

    def set_game_state_from_json(self, state_as_json):
        self.game_state = self.get_game_state_from_json(state_as_json)

    # TODO
    def player_to_bet(self, allowed_bets, game_state_json):
        logging.debug("Belote AI PLayer to bet: %s", self.player.name)
        logging.debug("Game state: %s", game_state_json)
        game_state = ContreeState(**json.loads(game_state_json))
        self.game_state = game_state

        self.game_state.active_player = self.game_state.next_player(self.game_state.dealer)
        #self.game_state.current_bet = "pass_0"

        if len(allowed_bets[0]) == 1 and allowed_bets[0][0] == "pass":
            return Announce("pass", 0)
        else:
            # Remove Pass option for simulation
            # self.game_state.allowed_bets[0].pop(0)
            bet_as_str = self._agent2.get_bet(self.game_state)

        logging.info("Agent calculated bet: %s", bet_as_str)
        if bet_as_str is None:
            return Announce("pass", 0)

        bet_points = -999
        if len(self.game_state.allowed_bets) == 1:
            print ("no allowed game points")

        nb_simulations = self._agent2.num_simulations_per_action[bet_as_str]
        if nb_simulations != 0:
            avg_points_for_bet = self._agent2.action_points[bet_as_str] / nb_simulations
            # Bet on avg_points_per_bet
            bet_points = round(avg_points_for_bet * ContreeAiPlayer.CORRECTION_FACTOR, -1)
            current_bet = Announce.from_str(self.game_state.current_bet)
            if bet_as_str == "contre_80":
                bet_points = 0
                if bet_points < BeloteGame.TOTAL_POINTS - current_bet.points:
                    bet_as_str = "pass_0"
                else:
                    bet_as_str = "contree_0"
            elif bet_as_str == "surcontre_80":
                bet_points = 0
                if bet_points < current_bet.points:
                    bet_as_str = "pass_0"
                else:
                    bet_as_str = "surcontree_0"
            elif bet_points < int(self.game_state.allowed_bets[1][0]):
                bet_points = 0
                bet_as_str = "pass_0"
            elif bet_points > BeloteGame.TOTAL_POINTS:
                bet_points = BeloteGame.TOTAL_POINTS

            logging.info("Avg points for bet: %s", avg_points_for_bet)
        else:
            logging.error(("Computed Bet has no simulation!!"))

        bet = Announce.from_str(bet_as_str)
        bet = Announce(bet.suit, bet_points)
        logging.info("Agent calculated bet: %s", str(bet))

        return bet

    def compute_bet_agent(self):
        return self._agent2.get_bet(self.game_state)


