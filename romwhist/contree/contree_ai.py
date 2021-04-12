import json
import logging

from contree.announce import Announce
from romwhist.contree.contree_state import ContreeState
from romwhist.belote.belote_ai import BeloteAiPlayer
from romwhist.ai.ai_agents import SimpleMCTSAgent
from romwhist.ai.ai_player import AiPlayer


# TODO: factorize with OhellAIPlayer
class ContreeAiPlayer(BeloteAiPlayer):

    def __init__(self, name, game_id):
        AiPlayer.__init__(self, name, game_id)
        self._agent = SimpleMCTSAgent('ContreeSim', name,
                                      action_chooser_function='random_action',
                                      num_simulations=100)

        self._agent2 = SimpleMCTSAgent('ContreeSim', name,
                                       action_chooser_function='random_action',
                                       num_simulations=100)

        self.game_state = ContreeState(game_id, self.name)

        #BeloteAiPlayer.__init__(self, name, game_id)

    def player_to_play(self, allowed_cards, game_state_json):
        game_state = ContreeState(**json.loads(game_state_json))
        self.game_state = game_state
        #self.game_state.allowed_cards = allowed_cards  # Unecessary

        # If only one action possible return it right away
        if len(self.game_state.allowed_cards) == 1:
            return self.game_state.allowed_cards[0]

        if len(self.game_state.allowed_cards) == 0:
            raise RuntimeError("Allowed cards is empty!")

        best_card = self._agent.get_action(self.game_state)

        # Select the card which result in the most points
        best_avg_points = 0
        for card in self.game_state.allowed_cards:
            points_for_card = self._agent.action_points[card]
            avg_points_for_card = 0
            if self._agent.num_simulations_per_action[card] > 0:
                avg_points_for_card = points_for_card / self._agent.num_simulations_per_action[card]
            logging.info("Avg points for card %s: %s", card, avg_points_for_card)
            if avg_points_for_card > best_avg_points:
                best_avg_points = max(best_avg_points, avg_points_for_card)
                best_card = card
        logging.info("Agent calculated card: %s", best_card)

        return best_card

    def set_game_state_from_json(self, state_as_json):
        self.game_state = ContreeState(**json.loads(state_as_json))

    # TODO
    def player_to_bet(self, allowed_bets, game_state_json):
        logging.debug("Belote AI PLayer to bet: %s", self.name)
        logging.debug("Game state: %s", game_state_json)
        game_state = ContreeState(**json.loads(game_state_json))
        self.game_state = game_state

        # Make active player the one that will start playing
        # for the simulated game
        self.game_state.active_player = self.game_state.next_player(self.game_state.dealer)

        # Remove Pass option
        # self.game_state.allowed_bets.pop(0)

        bet_as_str = self._agent2.get_bet(self.game_state)
        bet_points = -999
        nb_simulations = self._agent2.num_simulations_per_action[bet_as_str]
        if nb_simulations != 0:
            avg_points_for_bet = self._agent2.action_points[bet_as_str] / nb_simulations
            # Bet on avg_points_per_bet
            bet_points = round(avg_points_for_bet, -2)
            if bet_points < int(game_state.allowed_bets[0]):
                bet_points = 0
                bet_as_str = "Pass_0"
            logging.info("Agent calculated bet: %s", bet_as_str)
            logging.info("Avg points for this bet: %s", avg_points_for_bet)
        else:
            logging.error(("Computed Bet has no simulation!!"))

        bet = Announce.from_str(bet_as_str)
        bet = Announce(bet.suit, bet_points)
        return bet

    def compute_bet_agent(self):
        return self._agent2.get_bet(self.game_state)


