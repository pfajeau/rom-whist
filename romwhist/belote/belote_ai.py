import logging
import json

from romwhist.ai.ai_player import AiPlayer
from romwhist.ai.ai_agents import SimpleAgent, SimpleMCTSAgent, random_action
from romwhist.belote.belote_state import BeloteState

# TODO: factorize with OhellAIPlayer
class BeloteAiPlayer(AiPlayer):

    def __init__(self, name, game_id):
        AiPlayer.__init__(self, name, game_id)
        self.__agent = SimpleMCTSAgent('BeloteSim', name,
                                       action_chooser_function='random_action',
                                       num_simulations=100)

        self.__agent2 = SimpleMCTSAgent('BeloteSim', name,
                                       action_chooser_function='random_action',
                                       num_simulations=100)

        self.game_state = BeloteState(game_id, self.name)

    def player_to_play(self, allowed_cards, game_state_json):
        game_state = BeloteState(**json.loads(game_state_json))
        self.game_state = game_state
        #self.game_state.allowed_cards = allowed_cards  # Unecessary

        # If only one action possible return it right away
        if len(self.game_state.allowed_cards) == 1:
            return self.game_state.allowed_cards[0]

        if len(self.game_state.allowed_cards) == 0:
            raise RuntimeError("Allowed cards is empty!")

        best_card = self.__agent.get_action(self.game_state)

        # Select the card which result in the most points
        best_avg_points = 0
        for card in self.game_state.allowed_cards:
            points_for_card = self.__agent.action_points[card]
            avg_points_for_card = 0
            if self.__agent.num_simulations_per_action[card] > 0:
                avg_points_for_card = points_for_card / self.__agent.num_simulations_per_action[card]
            logging.info("Avg points for card %s: %s", card, avg_points_for_card)
            if avg_points_for_card > best_avg_points:
                best_avg_points = max(best_avg_points, avg_points_for_card)
                best_card = card
        logging.info("Agent calculated card: %s", best_card)

        return best_card

    def set_game_state_from_json(self, state_as_json):
        self.game_state = BeloteState(**json.loads(state_as_json))

    def player_to_bet(self, allowed_bets, game_state_json):
        logging.debug("Belote AI PLayer to bet: %s", self.name)
        logging.debug("Game state: %s", game_state_json)
        game_state = BeloteState(**json.loads(game_state_json))
        self.game_state = game_state

        # Make active player the one that will start playing
        # for the simulated game
        self.game_state.active_player = self.game_state.next_player(self.game_state.dealer)

        # Remove Pass option
        self.game_state.allowed_bets.pop(0)

        bet = self.__agent2.get_bet(self.game_state)

        nb_simulations = self.__agent2.num_simulations_per_action[bet]
        nb_wins_for_best_bet = self.__agent2.action_value[bet]
        ratio_win = nb_wins_for_best_bet/nb_simulations
        logging.info("Agent calculated bet: %s", bet)
        logging.info("Ratio of wins for that bet: %s", ratio_win)

        # Only take if the bet will lead to a significant number of wins
        if ratio_win > 0.75:
            return bet
        else:
            return allowed_bets[0]


    def compute_bet_agent(self):
        return self.__agent2.get_bet(self.game_state)


