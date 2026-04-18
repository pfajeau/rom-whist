"""
This module implements test common functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from romwhist.card import Card
from romwhist.hand import Hand


def create_hands(game, player_cards):
    for player in player_cards:
        hand = Hand(game.deck, 0)
        for card_as_str in player_cards[player]:
            hand.add(Card.card_from_value(card_as_str))
        game.hands[game.get_player_by_name(player)] = hand


def play_round(game, game_round, fc=""):
    active_player = game.get_active_player()
    for i in range(len(game.players)):
        print("Allowed cards for " + active_player + " : {}".format(game.get_allowed_cards(active_player)))
        if i == 0 and fc != "":
            game.play_card(active_player, fc)
        else:
            game.play_card(active_player, game.get_allowed_cards(active_player)[0])
        active_player = game.get_active_player()
    return game_round.winning_player
