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

from romwhist.belote.belote import BeloteGame
from romwhist.belote.belote_state import BeloteState
from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.hand import Hand


class BeloteSim(BeloteGame):

    def __init__(self, agent, other_agent, sim_player,
                 state: BeloteState = None, starting_action=None, one_round_only= False):
        BeloteGame.__init__(self, state.owner, id=state.game_id)
        self.sim_player = sim_player

        self.starting_action = starting_action
        self.first_play = True
        self.agent = agent
        self.other_agent = other_agent
        self.games_counter = [0, 0]
        self.one_round_only = one_round_only
        self.active_player = self.sim_player

        if state is not None:
            state_copy = copy.deepcopy(state)
            self.players = state.players
            self.soft_init_dict(state_copy.bets, "")
            self.populate_from_state(state_copy)

    def play_single_move(self):
        logging.debug("Simulating single move for player %s", self.active_player)
        #current_state = BeloteState(self.id, self.sim_player)
        current_state = self.get_state()
        #the_state = self.get_state(self.initial_state)

        if self.first_play and self.starting_action is not None:
            card = self.starting_action
            self.first_play = False
        elif self.active_player == self.sim_player:
            card = self.agent.get_action(current_state)
        else:
            card = self.other_agent.get_action(current_state)

        logging.debug("Player %s plays %s", self.active_player, str(card))
        winner = self.play_card(self.active_player, card)
        if winner is not None:
            logging.debug("Winner round: %s", winner)
        return winner

    def game_loop(self) -> None:
        logging.debug("Starting game_loop. Acive player is %s", self.active_player)
        logging.debug("Game phase is %s", self.phase)
        current_state = self.get_state()
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()

        # Remove sim players cards from deck
        for card in self.hands.get(self.sim_player).cards:
            self.deck.remove_card(card)

        if self.phase == BeloteGame.GamePhase.BET or self.phase == BeloteGame.GamePhase.BET2:
            self.place_bet(self.sim_player, self.bets[self.sim_player], ai=True)

            # Re-create hands from deck for other players for the simulation
            self.deck.remove_card(self.trump_card)
            for player in self.players:
                if player != self.sim_player:
                    self.hands[player] = Hand(self.deck, self.nb_cards_first_deal[len(self.players)])

            self.set_cards_rank_and_value()
            self.deal_2()
        else:
            # Remove from deck all cards that have been played
            # of the simulation
            cards_played_per_player = current_state.cards_played_per_player
            for player in self.players:
                cards_played = cards_played_per_player.get(player)
                if cards_played is not None:
                    for card in cards_played:
                        self.deck.remove_card(Card.card_from_value(card))

            # cards_current_round = self.current_round.get_cards_played()
            # for card in cards_current_round:
            #     if card is not None:
            #         self.deck.add_top(card)

            for player in self.players:
                if player != self.sim_player:
                    self.hands[player] = Hand(self.deck, len(self.hands[player].cards))
                logging.debug("In sim, Hand for player %s: %s", player, self.hands[player].serialize())

            # Required
            self.set_cards_rank_and_value()

        # Determine of AI player is first to play i current round
        ai_player_is_first_to_play = True
        for player in self.players:
            if self.current_round.cards_played.get(player) is not None:
                ai_player_is_first_to_play = False

        winner = None
        if self.current_round is None:
            logging.debug("Creating current round")
            round = self.create_round()

        self.phase = BeloteGame.GamePhase.PLAY

        # Play the current round
        logging.debug("PLaying current round")
        while winner is None:
            logging.debug ("Current round cards played: %s", self.current_round.get_cards_played())
            winner = self.play_single_move()

        # In this case we simulate the entire hand instead of just one round
        if not self.one_round_only:  #or ai_player_is_first_to_play:
            # Play other rounds until end of hand
            logging.debug("Playing other rounds in hand")
            while not self.is_hand_completed():
                round = self.create_round()
                round.trump_suit = self.trump_suit
                self.play_round(round)

            self.hand_completed()

        else:
            # Hand points need to be made equal to the round points for the simulation
            # to select the right action
            round_points = self.points_for_round((self.current_round))
            self.hand_winner.clear()

            if len(self.players) < 4:
                if self.sim_player == winner:
                    self.hand_points[self.sim_player] = round_points
                    self.hand_winner.append(self.sim_player)
                else:
                    self.hand_points[self.sim_player] = 0

            elif len(self.players) == 4:
                partner = self.next_player(self.next_player(self.sim_player))
                if self.sim_player == winner or partner == winner:
                    self.hand_points[self.sim_player] = round_points
                    self.hand_points[partner] = round_points
                    self.hand_winner.append(self.sim_player)
                    self.hand_winner.append(partner)

        logging.debug("End game_loop")
        return

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