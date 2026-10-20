"""
This module implements contree sim functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import logging
import copy

from romwhist.belote.belote_sim import BeloteSim
from romwhist.contree.contree import ContreeGame
from romwhist.contree.contree_state import ContreeState
from romwhist.contree.announce import Announce, ContreStatus


class ContreeSim(BeloteSim, ContreeGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: ContreeState = None, starting_action=None,
                 one_round_only=False, seed=None):
        ContreeGame.__init__(self, state.owner, id=state.game_id)
        BeloteSim.__init__(self, agent, other_agent, sim_player, state,
                           starting_action, one_round_only, seed)

        # Required because BeloteSim.__init__ calls BeloteGame.__init__,
        # which sets those to the belote values rather than the contree values
        self.nb_cards_first_deal = {1: 8, 2: 8, 3: 8, 4: 8}
        self.BONUS_CAPOT = 250

    def _start_bidding_rollout(self):
        bet = self.bets[self.sim_player]
        if bet.suit == 'pass':
            if self.current_bet is None or self.current_bet.suit == 'pass':
                raise ValueError('A pass without an existing contract has no hand to simulate')
            self.phase = self.GamePhase.PLAY
            self.active_player = self.next_player(self.dealer)
            self.update_belote_status()
        else:
            self.place_bet(self.sim_player, bet, ai=True)

    def evaluate_contract(self, action):
        """Score another bid on the same rollout, preserving the scoring mode."""
        game = copy.copy(self)
        bet = Announce.from_str(action)
        if bet.suit not in ('pass', 'contre', 'surcontre'):
            game.current_bet = bet
            game.taker = game.get_player_by_name(self.sim_player)
            game.contree_status = ContreStatus.NORMAL
        game.hand_points = self.final_card_points.copy()
        game.belote_status = self.final_belote_status
        game.scores = self.initial_scores.copy()
        game.scoresheet = []
        game._hand_scored = False
        game.update_scores()
        return game.score_difference(), game.sim_player in game.hand_winner

    def sim_player_won(self):
        logging.debug("Bet for %s: %s", self.sim_player, self.bets[self.sim_player])
        sim_player_wins = (self.sim_player in self.hand_winner)
        logging.debug("Wins: %s", sim_player_wins)
        return sim_player_wins

    def game_loop(self):
        BeloteSim.game_loop(self)
