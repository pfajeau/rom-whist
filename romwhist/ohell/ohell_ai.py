"""
This module implements ohell ai functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import json
import logging

from romwhist.ai.ai_agents import SimpleMCTSAgent
from romwhist.ai.ai_player import AiPlayer
from romwhist.ohell.ohell_state import OhellState


class OhellAiPlayer(AiPlayer):

    def __init__(self, name, game_id):
        AiPlayer.__init__(self, name, game_id)

        self.__agent = SimpleMCTSAgent('OhellSim', name,
                                       action_chooser_function='random_action',
                                       num_simulations=100)
        self.__agent2 = SimpleMCTSAgent('OhellSim', name,
                                       action_chooser_function='random_action',
                                       num_simulations=100)
        self.game_state = OhellState(game_id, self.player.name)


    def new_hand(self, cards):
        super().new_hand(cards)
        # self.state.nb_rounds_won = 0
        # self.state.bets = dict()
        #
        # for player in self.state.players:
        #     self.state.bets[player] = ""

    def player_to_bet(self, allowed_bets, game_state_json):
        logging.debug("Ohell AI PLayer to bet: %s", self.player.name)
        logging.debug("Game state: %s", game_state_json)

        # If only one bet allowed, can return it right away
        # TODO

        game_state = OhellState(**json.loads(game_state_json))
        self.game_state = game_state
        logging.debug("In player_to_bet, state is %s", game_state.to_json())
        # Make active player the one that will start playing
        # for the simulated game
        self.game_state.active_player = self.game_state.next_player(self.game_state.dealer)

        # bet1 = self.compute_bet_heuristics()
        best_bet = self.compute_bet_agent()

        # Select the bet which result in the most points
        # as there could be cases where no card leads to a win
        # best_avg_points = 0
        # for bet in game_state.get_legal_bets():
        #     points_for_bet = self.__agent2.action_points.get(bet)
        #     avg_points_for_bet = 0
        #     if self.__agent2.num_simulations_per_action.get(bet) > 0:
        #         avg_points_for_bet = points_for_bet / self.__agent2.num_simulations_per_action.get(bet)
        #     logging.info("Avg points for card %s: %s", bet, avg_points_for_bet)
        #     if avg_points_for_bet > best_avg_points:
        #         best_avg_points = max(best_avg_points, avg_points_for_bet)
        #         best_bet = bet

        logging.info("Agent calculated bet: %s", best_bet)
        return int(best_bet)

    def compute_bet_heuristics(self):
        my_hand = self.game_state.hand_cards[self.name]
        logging.info("Ohell Player %s hand: %s", self.name, self.game_state.hand_cards[self.name])
        allowed_bets = []

        # Convert bets to ints
        for i in range(0, len(self.game_state.allowed_bets)):
            allowed_bets.append(int(self.game_state.allowed_bets[i]))

        logging.info("Ohell Player %s allowed bets: %s", self.name, self.game_state.allowed_bets)

        self.compute_deck_value()
        nr = self.game_state.deck_size / 4
        cv = dict()
        vh = 0
        for card in my_hand:
            cv[str(card)] = self.compute_card_value(str(card))
            vh += cv[str(card)]
        logging.debug("Hand value: %s", vh)

        # Calculate average value of hand
        avh = len(my_hand) * self.vd / self.game_state.deck_size
        logging.debug("Average value of hand: %s", avh)

        np = len(self.game_state.players)
        ab = len(my_hand) / np
        bet = ab * vh / avh
        logging.info("Calculated bet: %s", bet)

        # Round and adjust to make it valid
        bet_int = int(round(bet))
        if bet_int in allowed_bets:
            return bet_int
        else:
            # Find closest allowed bet to bet
            for abet in allowed_bets:
                if abs(abet - bet) < 1:
                    return abet

        logging.error("Could not compute bet")
        return -1

    def compute_bet_agent(self):
        best_bet = self.__agent2.get_bet(self.game_state)
        if best_bet is None:
            return self.__agent2.best_action
        else:
            return best_bet

    def player_to_play(self, allowed_cards, game_state_json):
        game_state = OhellState(**json.loads(game_state_json))
        self.game_state = game_state

        # If only one action possible return it right away
        if len(self.game_state.allowed_cards) == 1:
            return self.game_state.allowed_cards[0]

        best_card = self.__agent.get_action(self.game_state)

        if best_card is None:
            # Pick a card at random from allowed cards
            return self.game_state.allowed_cards[0]

        # Select the card which result in the most points
        # as there could be cases where no card leads to a win
        # TODO: criteria should be to optimize the number of points between
        # the AI player and the other players.
        # I.e max(score(ai_player) - score (second best score)
        best_avg_points = 0
        for card in allowed_cards:
            points_for_card = self.__agent.action_points[card]
            avg_points_for_card = 0
            if self.__agent.num_simulations_per_action[card] > 0:
                avg_points_for_card = points_for_card / self.__agent.num_simulations_per_action[card]
            logging.info("Avg points for card %s: %s", card, avg_points_for_card)
            if avg_points_for_card > best_avg_points:
                best_avg_points = max(best_avg_points, avg_points_for_card)
                best_card = card
        logging.info("Agent calculated card: %s", best_card)
        return best_card

    @staticmethod
    def get_game_state_from_json(state_as_json):
        state = OhellState(**json.loads(state_as_json))
        return state

    # TODO: can be removed and put in base class?
    def set_game_state_from_json(self, state_as_json):
        self.game_state = self.get_game_state_from_json(state_as_json)


    def compute_card_value(self, card):
       # No trump.
       if self.game_state.trump == "" or self.game_state.trump is None:
           rank_win = round(len(self.game_state.hand_cards[self.name]) / 4)
           cv = 0
           for i in range(0,rank_win):
               for suit in ['c', 'h', 'd', 's']:
                   a_card = suit + str(14-i)
                   # TODO: if second highest card is the only one of that suit, don't assign it points
                   if a_card == str(card):
                       cv = 100/(i+1)
                       break
           logging.debug("Card value for %s is: %s", card, cv)

       else:
           cv = AiPlayer.compute_card_value(self, card)

       return cv
