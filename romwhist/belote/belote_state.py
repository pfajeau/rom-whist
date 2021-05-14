from romwhist.game_state import GameState
from romwhist.belote.belote_status import BeloteStatus


class BeloteState(GameState):
    def __init__(self, game_id, sim_player=None, players=[], trump="", cards_played_per_player=dict(),
                 cards_played_per_round=dict(), deck_size=0,
                 hand_cards=dict(), allowed_cards=[], active_player="", scores=dict(),
                 owner="", dealer = "",
                 bets=dict(), allowed_bets=[], trump_card = "",
                 phase = None, hand_points=dict(), hand_winner=[], taker=None,
                 belote_status=BeloteStatus.Not_Allowed):

        super().__init__(game_id, sim_player=sim_player, players=players, trump=trump,
                         cards_played_per_player=cards_played_per_player,
                         cards_played_per_round=cards_played_per_round, deck_size=deck_size,
                         hand_cards=hand_cards, allowed_cards=allowed_cards, active_player=active_player, scores=scores,
                         owner=owner, dealer=dealer, bets=bets, allowed_bets=allowed_bets, trump_card=trump_card,
                         hand_points=hand_points)
        self.phase = phase
        self.hand_points = hand_points
        self.hand_winner = hand_winner
        self.taker = taker
        self.belote_status = belote_status
