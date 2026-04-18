"""
This module implements test ohell functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import json
import logging
from romwhist.ohell.ohell import OhellGame
from romwhist.ohell.ohell_state import OhellState
from romwhist.card import Card
from romwhist.player import Player

from tests import test_common


def init_game(game_creator, player_names, game_id):
    ohell_game = OhellGame(game_creator, deck_size=32, id=game_id)
    for player_name in player_names:
        player = Player(player_name)
        ohell_game.add_player(player)

    ohell_game.start_game()
    ohell_game.set_hand_prgression(False, True, 2)
    ohell_game.create_hand_progression()
    ohell_game.active_player = game_creator

    return ohell_game

def main():
    logging.basicConfig(filename="test_ohell.log",
                        format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s",
                        level=logging.DEBUG)
    player_names = ["Joe", "Jack", "Jim", "Johnny"]
    players_by_name = dict()
    players = []
    Joe = Player("Joe")

    ohell = OhellGame(Joe)

    for player_name in player_names:
        player = Player(player_name)
        ohell.add_player(player)
        players_by_name[player_name] = player
        players.append(player)

    Joe = players_by_name["Joe"]
    Jack = players_by_name["Jack"]
    Jim = players_by_name["Jim"]
    Johnny = players_by_name["Johnny"]

    ohell.set_hand_prgression()
    ohell.start_game()
    ohell.create_hand_progression()
    ohell.set_hand_prgression(True, True, 1)
    ohell.create_hand_progression()
    ohell.set_hand_prgression(False, False, 1)
    ohell.create_hand_progression()
    ohell.set_hand_prgression(False, False, 2)
    ohell.create_hand_progression()
    ohell.deal(dealer=None)
    assert (not ohell.trump_card is None)
    assert (not ohell.trump_suit is None)
    ohell.deal(dealer=None)
    assert (not ohell.trump_card is None)
    assert (not ohell.trump_suit is None)
    ohell.deal(dealer=None)
    assert (not ohell.trump_card is None)
    assert (not ohell.trump_suit is None)
    ohell.deal(dealer=None)
    assert (not ohell.trump_card is None)
    assert (not ohell.trump_suit is None)
    ohell.deal(dealer=None)
    assert (ohell.trump_card is None)
    assert (ohell.trump_suit is None)

    # Testing game play
    for player in players:
        ohell.place_bet(player, 1)

    cards_played = ohell.get_cards_played_current_round()
    assert (cards_played is None)

    # Simulate a game and check scoring works
    # First use a pre-defined set of cards for each player
    cards_as_str = dict()
    cards_as_str["Joe"] = ['s9', 's10', 's11', 's14', 'h7', 'h10', 'c8', 'd9']
    cards_as_str["Jack"] = ['s7', 's8', 'h13', 'h11', 'c9', 'c10', 'd7', 'd13']
    cards_as_str["Jim"] = ['s12', 's13', 'h8', 'h9', 'c11', 'c12', 'd10', 'd14']
    cards_as_str["Johnny"] = ['h12', 'h14', 'c7', 'c13', 'c14', 'd8', 'd11', 'd12']

    test_common.create_hands(ohell, cards_as_str)
    ohell.active_player = Joe

    logging.debug("Playing Hand...")
    for i in range(8):
        logging.debug("    Playing round: " + str(i))
        round = ohell.create_round()
        winner = test_common.play_round(ohell, round)
        logging.debug("Winner for round " + str(i) + " is " + ohell.current_round.winning_player)

        cards_played = ohell.get_cards_played_current_round()
        logging.debug("Displaying last round cards")
        for player in cards_played:
                logging.debug(player + " played: " + str(cards_played[player]))

    ohell.hand_completed()
    scores = ohell.get_scores()
    logging.debug("Scores: ")
    for player in players:
        logging.debug(player + ": " + format(scores[player]))

    # Test scores
    ohell = OhellGame("Joe", 1, 32)
    for player_name in player_names:
        ohell.add_player(player_name)

    ohell.scores = {Joe: 1, Jack: 2, Jim: 0, Johnny: -1}
    winners = ohell.get_highest_score_player()
    assert (len(winners) == 1)
    assert (winners[0] == Jack)
    logging.debug(winners)

    ohell.scores = {Joe: 1, Jack: 2, Jim: 0, Johnny: 2}
    winners = ohell.get_highest_score_player()
    assert (len(winners) == 2)
    assert (winners[0] == Jack)
    assert (winners[1] == Johnny)
    logging.debug("Winners: " + str(winners))

    # Test Game state
    logging.debug("Testing Game State")
    ohell = init_game(Joe, player_names, "game_state_test")

    ohell.deal(dealer=None)
    ohell.deal(dealer=None)
    ohell.deal(dealer=None)
    ohell.deal(dealer=None)
    ohell.deal(dealer=None)

    cards_as_str = dict()
    cards_as_str["Joe"] = ['s9', 's10', 's11', 's14', 'h7', 'c8', 'd9']
    cards_as_str["Jack"] = ['s7', 's8', 'h13', 'h11', 'c10', 'd7', 'd13']
    cards_as_str["Jim"] = ['s12', 's13', 'h8', 'h9', 'c12', 'd10', 'd14']
    cards_as_str["Johnny"] = ['h12', 'h14', 'c7', 'c13', 'd8', 'd11', 'd12']

    test_common.create_hands(ohell, cards_as_str)
    ohell.active_player = Joe
    for player in players:
        ohell.place_bet(player, 1)

    ohell.trump_suit = 'Heart'
    ohell.trump_card = Card.card_from_value('h10')

    logging.debug("Starting Hand...")
    for i in range(4):
        logging.debug("    Playing round: " + str(i))
        round = ohell.create_round()
        winner = test_common.play_round(ohell, round)
        logging.debug("Winner for round " + str(i) + " is " + ohell.current_round.winning_player)

        cards_played = ohell.get_cards_played_current_round()
        logging.debug("Displaying last round cards")
        for player in cards_played:
            logging.debug(player + " played: " + str(cards_played[player]))

    # state = OhellState("8", joe)
    state = ohell.get_state()
    logging.debug("State: " + repr(state))
    ohell.populate_from_state(state)

    # Check that game can resume
    for i in range(5,8):
        logging.debug("    Playing round: " + str(i))
        round = ohell.create_round()
        winner = test_common.play_round(ohell, round)
        logging.debug("Winner for round " + str(i) + " is " + ohell.current_round.winning_player)

        cards_played = ohell.get_cards_played_current_round()
        logging.debug("Displaying last round cards")
        for player in cards_played:
            logging.debug(player + " played: " + str(cards_played[player]))

    ohell.hand_completed()
    scores = ohell.get_scores()

    # Test Sim Game
    logging.debug("Testing Sim Game")
    game_id = "sim_game"
    ohell = init_game(Joe, player_names, game_id)

    ohell.deal(dealer=None)
    ohell.deal(dealer=None)
    ohell.deal(dealer=None)
    for player in players:
        ohell.place_bet(player, 1)


    # state = OhellState("game_id", joe)
    ohell.get_state()
    logging.debug("Game state is: %s", state)

    #Test serialization
    state_dict = state.__dict__
    logging.debug("Game state as dict: %s", state_dict)
    state_json = json.dumps(state_dict)
    logging.debug("Game state as JSON: %s", state_json)
    game_state = OhellState(**json.loads(state_json))
    logging.debug("Game state from JSON as dict: %s", game_state.__dict__)


    # ai_agent = SimpleMCTSAgent("OhellSim", ai_player="Joe")
    # #sim_game = OhellSim(SimpleAgent(), SimpleAgent(), "Joe", state=state)
    # sim_game = OhellSim(ai_agent, SimpleAgent("Joe"), "Joe", state=state)
    # sim_game.run()


if __name__ == '__main__':
    main()





