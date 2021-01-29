import logging

from romwhist.game_state import GameState

class OhellState(GameState):
    def __init__(self, game_id, sim_player, players=[], trump="", cards_played_per_player=None,
                 cards_played_per_round=None, deck_size=0,
                 hand_cards=None, allowed_cards=[], active_player="",
                 bets=None, nb_rounds_won=0):

        super().__init__(game_id, sim_player, players, trump, cards_played_per_player,
                 cards_played_per_round, deck_size,
                 hand_cards, allowed_cards, active_player)
        self.bets = bets
        self.nb_rounds_won = nb_rounds_won


