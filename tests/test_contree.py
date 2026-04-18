"""
This module implements test contree functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import copy
import logging

from romwhist.belote.belote import BeloteGame
from romwhist.contree.announce import Announce
from romwhist.contree.contree import ContreeGame, CountingMethod
from romwhist.player import Player

from tests import test_common


def main():
    logging.basicConfig(filename='test_contree.log',
                        format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s",
                        level=logging.DEBUG)

    player_names = ["Joe", "Jack", "Jim", "Johnny"]
    players_by_name = dict()
    players = []
    Joe = Player("Joe")

    contree = ContreeGame(Joe)
    for player_name in player_names:
        player = Player(player_name)
        contree.add_player(player)

        players_by_name[player.name] = player
        players.append(player)

    Joe = players_by_name["Joe"]
    Jack = players_by_name["Jack"]
    Jim = players_by_name["Jim"]
    Johnny = players_by_name["Johnny"]

    assert (len(contree.get_playing_players()) == 4)
    assert contree.bets[Joe].suit == "", contree.bets[Joe].suit
    assert contree.bets[Joe].points == 0, contree.bets[Joe].points
    contree.start_game()

    contree.deal(dealer=Johnny)
    assert (contree.trump_suit is None)
    assert contree.active_player == Joe, contree.active_player
    for player in players:
        assert (len(contree.get_hand(player).cards) == 8)

    # self.assertEqual(True, False)

    # Test Place Bet
    assert len(contree.get_allowed_bets(Joe)[0]) == 5, len(contree.get_allowed_bets(Joe)[0])
    assert (len(contree.get_allowed_bets(Joe)[1]) == len(ContreeGame.all_bet_points))
    bet = Announce("spade", 80)
    contree.place_bet(Joe, bet)
    assert contree.next_player_to_bet(Joe, "_0") == Jack, contree.next_player_to_bet(Joe, "_0")
    assert contree.active_player == Jack, contree.active_player

    assert len(contree.get_allowed_bets(Jack)[0]) == 6, len(contree.get_allowed_bets(Jack)[0])
    assert len(contree.get_allowed_bets(Jack)[1]) == len(ContreeGame.all_bet_points) - 1, len(
        contree.get_allowed_bets(Jack)[1])
    bet = Announce("heart", 90)
    contree.place_bet(Jack, bet)
    assert contree.active_player == Jim, contree.active_player

    assert (len(contree.get_allowed_bets(Jim)[0]) == 6)
    assert (len(contree.get_allowed_bets(Jim)[1]) == len(ContreeGame.all_bet_points) - 2)
    bet = Announce("contre", 0)
    contree.place_bet(Jim, bet)
    assert contree.active_player == Johnny, contree.active_player
    assert contree.phase == BeloteGame.GamePhase.BET, contree.phase

    assert (len(contree.get_allowed_bets(Johnny)[0]) == 2)
    assert contree.get_allowed_bets(Johnny)[0][1] == "surcontre", contree.get_allowed_bets(Johnny)[0][1]
    # assert contree.get_allowed_bets(Johnny)[1][0] == 0, contree.get_allowed_bets(Johnny)[1][0]
    bet = Announce("surcontre", 0)
    contree.place_bet(Johnny, bet)
    assert contree.active_player == Joe, contree.active_player
    assert contree.phase == BeloteGame.GamePhase.PLAY, contree.phase

    # Test case where player that toook get contred and then passes on his turn
    contree = ContreeGame(Joe)
    for player in players:
        contree.add_player(player)
    contree.start_game()
    contree.deal(dealer=Johnny)
    bet = Announce("spade", 80)
    contree.place_bet(Joe, bet)
    bet = Announce("contre", 0)
    contree.place_bet(Jack, bet)
    bet = Announce("pass", 0)
    contree.place_bet(Jim, bet)
    bet = Announce("pass", 0)
    contree.place_bet(Jim, bet)
    contree.place_bet(Johnny, bet)
    assert contree.active_player == Joe, contree.active_player
    contree.place_bet(Joe, bet)
    assert contree.phase == BeloteGame.GamePhase.PLAY, contree.phase
    assert contree.bets[Joe].suit == "pass", contree.bets[Joe].suit

    # Similar test but Joe surcontre at the end
    contree = ContreeGame(Joe)
    for player in players:
        contree.add_player(player)
    contree.start_game()
    contree.deal(dealer=Johnny)
    bet = Announce("spade", 80)
    contree.place_bet(Joe, bet)
    bet = Announce("contre", 0)
    contree.place_bet(Jack, bet)
    bet = Announce("pass", 0)
    contree.place_bet(Jim, bet)
    bet = Announce("pass", 0)
    contree.place_bet(Jim, bet)
    bet = Announce("pass", 0)
    contree.place_bet(Johnny, bet)
    assert contree.active_player == Joe, contree.active_player
    bet = Announce("surcontre", 0)
    contree.place_bet(Joe, bet)
    assert contree.phase == BeloteGame.GamePhase.PLAY, contree.phase
    assert contree.bets[Joe].suit == "surcontre", contree.bets[Joe].suit

    # Simulate a game and check scoring works
    # First use a pre-defined set of cards for each player
    cards_as_str = dict()
    cards_as_str["Joe"] = ['s9', 's10', 's11', 's13', 'h7', 'h10', 'c8', 'd9']
    cards_as_str["Jack"] = ['s7', 's14', 'h13', 'h11', 'c9', 'c10', 'd7', 'd13']
    cards_as_str["Jim"] = ['s12', 's8', 'h8', 'h9', 'c11', 'c12', 'd10', 'd14']
    cards_as_str["Johnny"] = ['h12', 'h14', 'c7', 'c13', 'c14', 'd8', 'd11', 'd12']

    test_common.create_hands(contree, cards_as_str)

    # Set card values (were overwritten by new cards since they are different objects)
    contree.set_cards_rank_and_value()
    for i in range(1, 9):
        print("Creating new round")
        a_round = contree.create_round()
        winner = test_common.play_round(contree, a_round)
        print("Winner for round " + str(i) + " is " + contree.current_round.winning_player)

        cards_played = contree.get_cards_played_current_round()
        print("Displaying last round cards")
        for player in cards_played:
            print(player + " played: " + str(cards_played[player]))

    contree.hand_completed()
    scores = contree.get_scores()
    print("Scores: ", str(scores))

    contree = ContreeGame(Joe, counting=CountingMethod.POINTS_BID)
    for player in players:
        contree.add_player(player)
    contree.start_game()
    contree.deal(dealer=Johnny)
    bet = Announce("spade", 80)
    contree.place_bet(Joe, bet)
    bet = Announce("contre", 0)
    contree.place_bet(Jack, bet)
    bet = Announce("pass", 0)
    contree.place_bet(Jim, bet)
    bet = Announce("pass", 0)
    contree.place_bet(Jim, bet)
    contree.place_bet(Johnny, bet)
    assert contree.active_player == Joe, contree.active_player
    contree.place_bet(Joe, bet)
    assert contree.phase == BeloteGame.GamePhase.PLAY, contree.phase
    assert contree.bets[Joe].suit == "pass", contree.bets[Joe].suit

    test_common.create_hands(contree, cards_as_str)
    # Set card values (were overwritten by new cards since they are different objects)
    contree.set_cards_rank_and_value()
    for i in range(1, 9):
        print("Creating new round")
        a_round = contree.create_round()
        winner = test_common.play_round(contree, a_round)
        print("Winner for round " + str(i) + " is " + contree.current_round.winning_player)

        cards_played = contree.get_cards_played_current_round()
        print("Displaying last round cards")
        for player in cards_played:
            print(player + " played: " + str(cards_played[player]))

    for player in players:
        print("Player hand points for " + player + ": " + str(contree.hand_points[player]))
        print("Player total points for " + player + ": " + str(contree.get_scores()[player]))
    hand_points_joe = contree.hand_points[Joe]
    total_points_joe = contree.scores[Joe]
    hand_points_jack = contree.hand_points[Jack]
    total_points_jack = contree.scores[Jack]
    contree.hand_completed()
    for player in players:
        print("Player hand points for " + player + ": " + str(contree.hand_points[player]))
        print("Player total points for " + player + ": " + str(contree.get_scores()[player]))
    scores = contree.get_scores()
    assert scores[Joe] == 80 * 2 + total_points_joe, scores[Joe]
    assert scores[Jack] == 0, scores[Jack]
    assert scores[Jim] == scores[Joe], scores[Jim]
    assert scores[Johnny] == scores[Jack], scores[Johnny]

    print("Scores: ", str(scores))


if __name__ == '__main__':
    main()
