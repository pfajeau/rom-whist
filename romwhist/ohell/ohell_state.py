import logging

from romwhist.game_state import GameState

class OhellState(GameState):
    def __init__(self, game_id, sim_player=None, players=[], trump="", cards_played_per_player=dict(),
                 cards_played_per_round=dict(), deck_size=0,
                 hand_cards=dict(), allowed_cards=[], active_player="", scores=dict(),
                 owner="", dealer = "",
                 bets=dict(), nb_rounds_won=dict(), allowed_bets=[]):

        super().__init__(game_id, sim_player=sim_player, players=players, trump=trump, cards_played_per_player=cards_played_per_player,
                 cards_played_per_round=cards_played_per_round, deck_size=deck_size,
                 hand_cards=hand_cards, allowed_cards=allowed_cards, active_player=active_player, scores=scores,
                         owner=owner, dealer=dealer, allowed_bets=allowed_bets)
        self.bets = bets
        self.nb_rounds_won = nb_rounds_won


