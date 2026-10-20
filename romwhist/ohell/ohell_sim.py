"""
This module implements ohell sim functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import copy
import random

from romwhist.ohell.ohell import OhellGame
from romwhist.ohell.ohell_state import OhellState
from romwhist.ohell.ohell_strategy import WhistTacticalAgent, sample_hidden_hands


class OhellSim(OhellGame):
    def __init__(self, agent, other_agent, sim_player,
                 state: OhellState = None, starting_action=None,
                 one_round_only=False, seed=None):
        OhellGame.__init__(self, state.owner, id=state.game_id)
        self.sim_player = sim_player
        self.starting_action = starting_action
        self.first_play = True
        self.agent = agent
        self.other_agent = other_agent
        self.rng = random.Random(random.getrandbits(64) if seed is None else seed)
        self.initial_state = copy.deepcopy(state)
        self.populate_from_state(state)

    def _complete_bids(self):
        """Model unannounced bids from sampled hands; retain all actual bids."""
        policy = WhistTacticalAgent()
        player = self.next_player(self.dealer)
        total_cards = len(self.hands[player].cards) + sum(self.wins.values())
        for _ in self.players:
            if self.bets[player] < 0:
                allowed = list(range(total_cards + 1))
                if player == self.dealer:
                    forbidden = total_cards - sum(max(bet, 0) for bet in self.bets.values())
                    if forbidden in allowed:
                        allowed.remove(forbidden)
                self.bets[player] = policy.estimate_bid(self, player, allowed, self.rng)
            player = self.next_player(player)

    def play_single_move(self):
        if self.first_play and self.starting_action is not None:
            card = self.starting_action
            self.first_play = False
        else:
            agent = self.agent if self.active_player == self.sim_player else self.other_agent
            card = (agent.choose_card(self) if hasattr(agent, 'choose_card')
                    else agent.get_action(self.get_state()))
        return self.play_card(self.active_player, card)

    def game_loop(self):
        sample_hidden_hands(self, self.sim_player, self.rng)
        self._complete_bids()
        if self.phase == self.GamePhase.BET:
            self.active_player = self.next_player(self.dealer)
        self.phase = self.GamePhase.PLAY
        if self.current_round is None or self.current_round.last_card_played():
            self.create_round()
        # Exact-bid objectives require the whole hand, even when the caller
        # supplies the old one_round_only flag for compatibility.
        while not self.is_hand_completed():
            winner = self.play_single_move()
            if winner is not None and not self.is_hand_completed():
                self.create_round()
        self.hand_completed()
        self.evaluation_score = self.hand_points[self.sim_player]

    def play_round(self, round):
        winner = None
        while winner is None:
            winner = self.play_single_move()
        return winner

    def run(self):
        self.game_loop()
        return True

    def sim_player_won(self):
        return self.bets[self.sim_player] == self.wins[self.sim_player]

    def state(self):
        return self.get_state()
