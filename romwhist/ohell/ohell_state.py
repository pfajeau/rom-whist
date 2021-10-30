from romwhist.game_state import GameState

class OhellState(GameState):
    def __init__(self, game_id, sim_player=None, players=[], trump="", cards_played_per_player=dict(),
                 cards_played_per_round=dict(), deck_size=0, phase=None,
                 hand_cards=dict(), allowed_cards=[], active_player=None, scores=dict(),
                 owner=None, dealer = None, trump_card = "", hand_points=dict(),
                 bets=dict(), nb_rounds_won=dict(), allowed_bets=[],
                 players_status=dict(), players_type=dict()):

        super().__init__(game_id, sim_player=sim_player, players=players, trump=trump, cards_played_per_player=cards_played_per_player,
                 cards_played_per_round=cards_played_per_round, deck_size=deck_size,
                 hand_cards=hand_cards, allowed_cards=allowed_cards, active_player=active_player, scores=scores,
                 owner=owner, dealer=dealer,
                 bets=bets, allowed_bets=allowed_bets, trump_card=trump_card, hand_points=hand_points,
                 players_status=players_status, players_type=players_type)

        self.nb_rounds_won = nb_rounds_won
        self.phase = phase


