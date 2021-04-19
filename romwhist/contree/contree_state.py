from romwhist.card import Card
from romwhist.contree.announce import Announce, ContreStatus
from romwhist.belote.belote_state import BeloteState


class ContreeState(BeloteState):
    # Note: bets must be passed as a list of strings
    def __init__(self, game_id, sim_player=None, players=[], trump="", cards_played_per_player=dict(),
                 cards_played_per_round=dict(), deck_size=0,
                 hand_cards=dict(), allowed_cards=[], active_player="", scores=dict(),
                 owner="", dealer = "",
                 bets=dict(), allowed_bets=[], trump_card = "",
                 phase = None, hand_points=dict(), hand_winner=[], taker=None,
                 contree_status = ContreStatus.NORMAL, current_bet = "Pass_0"):

        BeloteState.__init__(self, game_id, sim_player=sim_player, players=players, trump=trump, cards_played_per_player=cards_played_per_player,
                 cards_played_per_round=cards_played_per_round, deck_size=deck_size,
                 hand_cards=hand_cards, allowed_cards=allowed_cards, active_player=active_player, scores=scores,
                 owner=owner, dealer=dealer, bets=bets, allowed_bets=allowed_bets, trump_card=trump_card,
                 phase=phase, hand_points=hand_points, hand_winner=hand_winner, taker=taker)

        self.contree_status = contree_status
        self.current_bet = current_bet

    def get_legal_bets(self):
        allowed = []

        for suit in Card.SUIT_NAMES:
        #     for bet_point in self.allowed_bets:
        #         allowed.append(ContreeGame.Announce(suit, bet_point))
            allowed.append(str(Announce(suit, 80)))
        # TODO: add Contree or Surcontree option
        return allowed
