import json
import logging

from romwhist.ai.ai_agents import SimpleMCTSAgent
from romwhist.ai.ai_player import AiPlayer
from romwhist.deck import Deck
from romwhist.belote.belote_state import BeloteState
from romwhist.belote.belote import BeloteGame


# TODO: factorize with OhellAIPlayer
class BeloteAiPlayer(AiPlayer):

    def __init__(self, name, game_id):
        AiPlayer.__init__(self, name, game_id)
        self._agent = SimpleMCTSAgent('BeloteSim', name,
                                      action_chooser_function='random_action',
                                      num_simulations=100)

        self._agent2 = SimpleMCTSAgent('BeloteSim', name,
                                       action_chooser_function='random_action',
                                       num_simulations=100)

        self.game_state = BeloteState(game_id, self.name)

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

        if best_card is None:
            fake_game = BeloteGame("")
            fake_game.trump_suit = self.game_state.trump
            fake_game.deck = Deck(self.game_state.deck_size)

            fake_game.set_cards_rank_and_value()

            # Return weakest card from allowed cards
            best_card = str(self.game_state.allowed_cards[0])
            min_points = fake_game.card_points[best_card]
            for card in self.game_state.allowed_cards:
                if fake_game.card_points[str(card)] < min_points:
                    best_card = card
                    min_points = fake_game.card_points[str(card)]
            logging.info ("No good card to play - Best card is: " + str(best_card))
            return best_card

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

        bet = self._agent2.get_bet(self.game_state)

        if bet is None:
            return "pass"

        nb_simulations = self._agent2.num_simulations_per_action[bet]
        nb_wins_for_best_bet = self._agent2.action_value[bet]
        ratio_win = 0
        if nb_simulations != 0:
            ratio_win = nb_wins_for_best_bet/nb_simulations

        logging.info("Agent calculated bet: %s", bet)
        logging.info("Ratio of wins for that bet: %s", ratio_win)

        # Only take if the bet will lead to a significant number of wins
        if ratio_win > 0.75:
            return bet
        else:
            return "pass"


    def compute_bet_agent(self):
        return self._agent2.get_bet(self.game_state)


