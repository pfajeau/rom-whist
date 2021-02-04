import logging

from romwhist.ai.ai_player import AiPlayer


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


    def player_to_bet(self, allowed_bets, game_state_json):
        logging.debug("Belote AI PLayer to bet: %s", self.name)
        logging.debug("Game state: %s", game_state_json)
        game_state = BeloteState(**json.loads(game_state_json))
        self.game_state = game_state

        # this is here because easier for testing.
        # allowed_bets shoud really come from the game state
        for bet in allowed_bets:
            self.game_state.allowed_bets.append(str(bet))

        bet = self.compute_bet_agent()
        logging.info("Agent calculated bet: %s", bet)
        return bet

    def compute_bet_agent(self):
        return self.__agent2.get_bet(self.game_state)

    def set_game_state_from_json(self, state_as_json):
       self.game_state =  BeloteState(**json.loads(state_as_json))

    # TODO
    def player_to_play(self, allowed_cards, game_state_json):
        game_state = BeloteState(**json.loads(game_state_json))
        self.game_state = game_state
        self.game_state.allowed_cards = allowed_cards
        return self.__agent.get_action(self.game_state)
