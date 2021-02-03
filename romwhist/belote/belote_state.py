import logging

from romwhist.game_state import GameState

class BeloteState(GameState, game_id):
    def __init__(self):
        GameState.__init__(self, game_id)