"""
This module implements contree state functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from romwhist.card import Card
from romwhist.contree.announce import Announce, ContreStatus
from romwhist.belote.belote_state import BeloteState
from romwhist.belote.belote_status import BeloteStatus


class ContreeState(BeloteState):
    # Note: bets must be passed as a list of strings
    def __init__(self, game_id, sim_player=None, players=[], trump="", cards_played_per_player=dict(),
                 cards_played_per_round=dict(), deck_size=0,
                 hand_cards=dict(), allowed_cards=[], active_player="", scores=dict(),
                 owner="", dealer = "",
                 bets=dict(), allowed_bets = None, trump_card = "",
                 phase = None, hand_points=dict(), hand_winner=[], taker=None,
                 contree_status = ContreStatus.NORMAL, current_bet = "pass_0", BONUS_CAPOT = 250,
                 belote_status=BeloteStatus.Not_Allowed,
                 players_status=dict(), players_type=dict()):

        BeloteState.__init__(self, game_id, sim_player=sim_player, players=players, trump=trump,
                             cards_played_per_player=cards_played_per_player,
                             cards_played_per_round=cards_played_per_round, deck_size=deck_size,
                             hand_cards=hand_cards, allowed_cards=allowed_cards, active_player=active_player,
                             scores=scores, owner=owner, dealer=dealer, bets=bets, allowed_bets=allowed_bets,
                             trump_card=trump_card, phase=phase, hand_points=hand_points, hand_winner=hand_winner,
                             taker=taker,belote_status=belote_status,
                             players_status=players_status, players_type=players_type)

        self.contree_status = contree_status
        self.current_bet = current_bet
        self.BONUS_CAPOT = BONUS_CAPOT   # Required for AI
        self.allowed_bets = allowed_bets

    def get_legal_bets(self):
        allowed = []
        for bet in self.allowed_bets[0]:
            if bet.casefold() != "PASS".casefold():
                allowed.append(str(bet) + "_80")
        return allowed
