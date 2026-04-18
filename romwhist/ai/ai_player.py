"""
This module implements ai player functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import logging

from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.player import Player


class AiPlayer:

    def __init__(self, player, id):
        self.vd = 0
        self.player = player
        self.__game_state = None
        self.player.player_type = Player.PlayerType.AI
        self.player.player_status = Player.PlayerStatus.ACTIVE
        self.game_id = id

    @property
    def game_state(self):
        return self.__game_state

    @game_state.setter
    def game_state(self, value):
        self.__game_state = value

    def game_started(self, deck_size, players):
        logging.debug("Game started. Deck size: %s", deck_size)
        # self.__deck_size = deck_size
        # self.game_state.players = players
        # #self.__deck_size=deck_size
        return

    def set_trump(self, trump_card, trump_suit):
        # self.trump_card = trump_card
        # self.game_state.trump = trump_suit
        return

    def player_to_bet(self, allowed_bets, game_state_json):
        return allowed_bets[0]

    def player_bet(self, player, bet):
        # self.game_state.bets[player] = bet
        return

    def player_to_play(self, allowed_cards, game_state_json):
        logging.debug("AI PLayer to play: %s", self.name)
        logging.debug("Allowed cards: %s", allowed_cards)
        # Retrieve state from data (as JASON)
        # self.game_state = OhellState()
        return allowed_cards[0]

    def card_played(self, player, card):
        # self.game_state.cards_played_per_player[player].append(card)
        # self.game_state.cards_played.append(card)
        # #self.game_state.cards_played_per_round.append(card)
        # self.game_state.deck.remove_card(card)
        # suit = Card.card_from_value(card).get_suit()
        # self.game_state.cards_played_by_suit[suit].append(card)
        return

    def new_hand(self, cards):
        # for card in cards:
        #     self.my_hand.append(Card.card_from_value(card))
        #     self._cards_as_str.append(card)
        # # self.game_state.hand_cards = []
        # self.game_state.cards_played_per_player = dict()
        #
        # for player in self.game_state.players:
        #     self.game_state.cards_played_per_player[player] = []
        #
        # self.game_state.deck = Deck(self.game_state.deck_size)
        # for card in cards:
        #     self.game_state.hand_cards.append(Card.card_from_value(card))
        # logging.debug("In new hand, cards: %s", len(self.my_hand))
        return

    def compute_deck_value(self):
        # Calculate average value of hand
        deck = Deck(self.game_state.deck_size)
        cards = deck.all_cards
        self.vd = 0
        for card in cards:
            self.vd += self.compute_card_value(str(card))
        logging.info("Deck value: %s", self.vd)
        return self.vd

    def compute_card_value(self, card):
        # Returns card value between 0 and 100
        my_card = Card.card_from_value(card)
        r = 14 - my_card.rank
        nr = self.game_state.deck_size / 4
        cv = ((nr - r) * 50) / 8

        logging.debug ("r: %s, nr: %s, deck_size: %s, cv: %s", r, nr, self.game_state.deck_size, cv)
        # Trump card: add 50 points
        if my_card.get_suit_name() == self.game_state.trump:
            cv += 50
        logging.debug("Card value for %s is: %s", card, cv)
        return cv


