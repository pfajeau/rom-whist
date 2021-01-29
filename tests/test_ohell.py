import logging
from romwhist.ohell.ohell import OhellGame
from romwhist.ohell.ohell_state import OhellState

from tests import test_common


if __name__ == '__main__':
    logging.basicConfig(filename="Tests_ohell.log",
                        format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s",
                        level=logging.DEBUG)

    players = ["Joe", "Jack", "Jim", "Johnny"]
    ohell = OhellGame("Joe")

    for player in players:
        ohell.add_player(player)
    ohell.set_hand_prgression()
    ohell.start_game()
    ohell.create_hand_progression()
    ohell.set_hand_prgression(True, True, 1)
    ohell.create_hand_progression()
    ohell.set_hand_prgression(False, False, 1)
    ohell.create_hand_progression()
    ohell.set_hand_prgression(False, False, 2)
    ohell.create_hand_progression()
    ohell.deal(dealer="")
    assert (not ohell.trump_card is None)
    assert (not ohell.trump_suit is None)
    ohell.deal(dealer="")
    assert (not ohell.trump_card is None)
    assert (not ohell.trump_suit is None)
    ohell.deal(dealer="")
    assert (not ohell.trump_card is None)
    assert (not ohell.trump_suit is None)
    ohell.deal(dealer="")
    assert (not ohell.trump_card is None)
    assert (not ohell.trump_suit is None)
    ohell.deal(dealer="")
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
    ohell.active_player = "Joe"

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
    for player in players:
        ohell.add_player(player)

    ohell.scores = {"Joe": 1, "Jack": 2, "Jim": 0, "Johnny": -1}
    winners = ohell.get_highest_score_player()
    assert (len(winners) == 1)
    assert (winners[0] == "Jack")
    logging.debug(winners)

    ohell.scores = {"Joe": 1, "Jack": 2, "Jim": 0, "Johnny": 2}
    winners = ohell.get_highest_score_player()
    assert (len(winners) == 2)
    assert (winners[0] == "Jack")
    assert (winners[1] == "Johnny")
    logging.debug("Winners: " + str(winners))

    # Test Game state
    logging.debug("Testing Game State")
    ohell = OhellGame("Joe", deck_size=32, id="8")
    for player in players:
        ohell.add_player(player)

    ohell.start_game()
    ohell.deal(dealer="")
    ohell.deal(dealer="")
    ohell.deal(dealer="")
    ohell.deal(dealer="")
    ohell.deal(dealer="")

    test_common.create_hands(ohell, cards_as_str)
    ohell.active_player = "Joe"
    for player in players:
        ohell.place_bet(player, 1)

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

    state = OhellState("8", "Joe")
    ohell.get_state(state)
    logging.debug("State: " + repr(state))
    ohell.set_state(state)

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


