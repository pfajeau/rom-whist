"""
This module implements belote sim functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import copy
import logging
import random

from romwhist.belote.belote import BeloteGame
from romwhist.belote.belote_state import BeloteState
from romwhist.belote.belote_status import BeloteStatus
from romwhist.card import Card
from romwhist.belote.belote_inference import sample_hidden_hands


class BeloteSim(BeloteGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: BeloteState = None, starting_action=None, one_round_only=False, seed=None):
        BeloteGame.__init__(self, state.owner, id=state.game_id)
        self.sim_player = sim_player

        self.starting_action = starting_action
        self.first_play = True
        self.agent = agent
        self.other_agent = other_agent
        self.games_counter = [0, 0]
        self.one_round_only = one_round_only
        self.rng = random.Random(random.getrandbits(64) if seed is None else seed)
        self.active_player = self.sim_player

        if state is not None:
            state_copy = copy.deepcopy(state)
            self.players = state.players
            self.soft_init_dict(state_copy.bets, "")
            self.populate_from_state(state_copy)

    def play_single_move(self):
        logging.debug("Simulating single move for player %s", self.active_player)
        if self.first_play and self.starting_action is not None:
            card = self.starting_action
            self.first_play = False
        else:
            agent = self.agent if self.active_player == self.sim_player else self.other_agent
            card = (agent.choose_card(self) if hasattr(agent, 'choose_card')
                    else agent.get_action(self.get_state()))

        logging.debug("Player %s plays %s", self.active_player, str(card))
        if self.active_player == self.player_with_belote and card in (
                Card.get_suit_initial(self.trump_suit) + "12",
                Card.get_suit_initial(self.trump_suit) + "13"):
            if self.belote_status == BeloteStatus.Allowed:
                self.player_announced_belote(self.active_player, self.BeloteAnnounced.BELOTE)
            elif self.belote_status == BeloteStatus.Belote_Played:
                self.player_announced_belote(self.active_player, self.BeloteAnnounced.REBELOTE)
        winner = self.play_card(self.active_player, card)
        if winner is not None:
            logging.debug("Winner round: %s", winner)
        return winner

    def _start_bidding_rollout(self):
        self.place_bet(self.sim_player, self.bets[self.sim_player], ai=True)
        self.deal_2()

    def score_difference(self):
        side = [self.sim_player]
        if len(self.players) == 4:
            side.append(self.next_player(self.next_player(self.sim_player)))
        opponents = [player for player in self.players if player not in side]
        own_gain = self.scores[self.sim_player] - self.initial_scores[self.sim_player]
        other_gain = max((self.scores[player] - self.initial_scores[player]
                          for player in opponents), default=0)
        return own_gain - other_gain

    def game_loop(self) -> None:
        self.initial_scores = self.scores.copy()
        betting = self.phase in (self.GamePhase.BET, self.GamePhase.BET2)
        sample_hidden_hands(self, self.sim_player, self.rng, betting=betting)
        if betting:
            self._start_bidding_rollout()
        self.set_cards_rank_and_value()
        if self.current_round is None:
            self.create_round()
        self.phase = self.GamePhase.PLAY

        winner = None
        while winner is None:
            winner = self.play_single_move()
        if not self.one_round_only:
            while not self.is_hand_completed():
                self.create_round()
                self.play_round(self.current_round)
            # Preserve unaggregated results for evaluating different contracts
            # on the same sampled deal, without replaying the hand each time.
            self.final_card_points = self.hand_points.copy()
            self.final_belote_status = self.belote_status
            self.hand_completed()
            self.evaluation_score = self.score_difference()
        else:
            round_points = self.points_for_round(self.current_round)
            if self.is_hand_completed():
                round_points += self.DIX_DE_DER
            winners = [winner]
            if len(self.players) == 4:
                winners.append(self.next_player(self.next_player(winner)))
            # A lost rollout must not retain points earned in previous tricks.
            self.hand_points = {player: round_points if player in winners else 0
                                for player in self.players}
            self._hand_winner = winners
            self.evaluation_score = round_points if self.sim_player in winners else -round_points

    def play_round(self, round):
        logging.debug("Playing round")
        winner = ""
        for i in range(len(self.get_playing_players())):
            winner = self.play_single_move()

        logging.debug("Round completed. Winner is %s", winner)
        return winner

    def run(self) -> bool:
        self.game_loop()
        return True

    def sim_player_won(self):
        logging.debug("Bet for %s: %s", self.sim_player, self.bets[self.sim_player])
        sim_player_wins = (self.sim_player in self.hand_winner)
        logging.debug("Wins: %s", sim_player_wins)
        return sim_player_wins

    def state(self):
        return self.get_state()
