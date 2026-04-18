"""
This module implements belote state functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import json
from romwhist.game_state import GameState
from romwhist.belote.belote_status import BeloteStatus


class BeloteState(GameState):
    def __init__(self, game_id, sim_player=None, players=[], trump="", cards_played_per_player=dict(),
                 cards_played_per_round=dict(), deck_size=0,
                 hand_cards=dict(), allowed_cards=[], active_player=None, scores=dict(),
                 owner=None, dealer = None,
                 bets=dict(), allowed_bets=[], trump_card = "",
                 phase = None, hand_points=dict(), hand_winner=[], taker=None,
                 belote_status=BeloteStatus.Not_Allowed,
                 players_status=dict(), players_type=dict()):

        super().__init__(game_id, sim_player=sim_player, players=players, trump=trump,
                         cards_played_per_player=cards_played_per_player,
                         cards_played_per_round=cards_played_per_round, deck_size=deck_size,
                         hand_cards=hand_cards, allowed_cards=allowed_cards, active_player=active_player, scores=scores,
                         owner=owner, dealer=dealer, bets=bets, allowed_bets=allowed_bets, trump_card=trump_card,
                         hand_points=hand_points,
                         players_status=players_status, players_type=players_type)
        self.phase = phase
        self.hand_winner = hand_winner
        if isinstance(taker, str):
            self.taker = taker
        elif taker is not None:
            self.taker = taker.name
        else:
            self.taker = None
        self.belote_status = belote_status


