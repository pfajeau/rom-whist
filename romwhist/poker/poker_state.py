"""
This module implements poker state functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import json

from romwhist.game_state import GameState


class PokerState(GameState):
    """Serializable state snapshot for a poker hand, passed to the AI process."""

    def __init__(self, game_id, sim_player=None, players=[], hand_cards={},
                 active_player=None, scores={}, owner=None, dealer=None,
                 players_status={}, players_type={},
                 community_cards=[], pot=0, current_bet=0,
                 bets_this_round={}, folded_players=[], money={},
                 phase=None, hole_cards_count=2, allowed_actions=[],
                 poker_type="texas_holdem", small_blind=10, big_blind=20,
                 # absorb extra GameState kwargs silently
                 **kwargs):
        super().__init__(
            game_id,
            sim_player=sim_player,
            players=players,
            hand_cards=hand_cards,
            active_player=active_player,
            scores=scores,
            owner=owner,
            dealer=dealer,
            players_status=players_status,
            players_type=players_type,
        )
        self.community_cards = community_cards
        self.pot = pot
        self.current_bet = current_bet
        self.bets_this_round = bets_this_round
        self.folded_players = folded_players
        self.money = money
        self.phase = phase
        self.hole_cards_count = hole_cards_count
        self.allowed_actions = allowed_actions
        self.poker_type = poker_type
        self.small_blind = small_blind
        self.big_blind = big_blind

    def get_legal_actions(self):
        return list(self.allowed_actions)

    def get_legal_bets(self):
        return list(self.allowed_actions)
