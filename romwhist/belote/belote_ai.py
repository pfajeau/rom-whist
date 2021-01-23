import logging

from romwhist.ai.ai_player import AiPlayer


class BeloteAiPlayer(AiPlayer):

    def __init__(self, name, game_id):
        AiPlayer.__init__(self, name, game_id)

    def player_to_bet(self, allowed_bets):
        return AiPlayer.player_to_play(self, allowed_cards)

    def player_to_play(self, allowed_cards):
        return AiPlayer.player_to_play(self, allowed_cards)
