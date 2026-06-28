"""
This module implements sim game functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import logging
from abc import abstractmethod
import copy

from romwhist.game import CardGame
from romwhist.game_state import GameState


class SimGame(CardGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: GameState = None, starting_action=None):
        """
        :param State state: Initial game state.
        :param Card starting_action: Initial play of current player.
            If None, chosen according to `agent`'s policy.
        """
        super().__init__()
        # state_copy = copy(state)
        #
        # self.game_id = state_copy.game_id
        # self.players = state_copy.players
        # self.trump = state_copy.trump
        # self.cards_played_per_player =  state_copy.cards_played_per_player
        # self.deck_size = state_copy.deck_size
        # self.hand_cards = state_copy.hand_cards
        # self.allowed_cards = state_copy.allowed_cards
        # self.active_player = state_copy.active_player

        self.sim_player = sim_player

        self.starting_action = starting_action
        self.first_play = True
        self.agent = agent  # type: IAgent
        self.other_agent = other_agent  # type: IAgent
        self.games_counter = [0, 0]
        self.initial_state = copy.deepcopy(state)


    def play_single_move(self):
        logging.debug("Playing single move")

        if self.first_play and self.starting_action is not None:
            card = self.starting_action
            self.first_play = False
        elif self.active_player == self.sim_player:
            card = self.agent.get_action(self.state())
        else:
            card = self.other_agent.get_action(self.state())

        winner = self.play_card(self.active_player, card)
        return winner

    @abstractmethod
    def state(self):
        raise NotImplementedError

    def game_loop(self) -> None:
        # Active player plays
        # until end of round
        # Then while there is still a card in hand
        # Play each round
        # Determine whether AI player won or not (game dependant)
        winner = None
        while winner is None:
            winner = self.play_single_move()

        # Play rounds until end of hand
        while not self.is_hand_completed():
            round = self.create_round()
            self.play_round(round)

        return


    def play_round(self):
        logging.debug("Playing round")
        self.active_player = self.get_active_player()
        winner = ""
        for i in range(len(self.get_playing_players())):
            winner = self.play_single_move()

        return winner

    @abstractmethod
    def sim_player_won():
        raise NotImplementedError


    def run(self) -> bool:
        self.game_loop()
        return True
