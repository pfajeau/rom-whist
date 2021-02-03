import logging

from romwhist.ai.ai_player import AiPlayer


class BeloteAiPlayer(AiPlayer):

    def __init__(self, name, game_id):
        AiPlayer.__init__(self, name, game_id)

    def player_to_bet(self, allowed_bets, game_state_json):
        # TODO
        return allowed_bets[0]   # Pass option

    # TODO
    def player_to_play(self, allowed_cards, game_state_json):
        return AiPlayer.player_to_play(self, allowed_cards, game_state_json)
