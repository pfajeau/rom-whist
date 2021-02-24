import json
import logging
from romwhist.ohell.ohell import OhellGame
from romwhist.ohell.ohell_state import OhellState
from romwhist.card import Card

from tests import test_common


def init_game(players, game_id):
    ohell_game = OhellGame("Joe", deck_size=32, id=game_id)
    for player in players:
        ohell_game.add_player(player)

    ohell_game.start_game()
    ohell_game.set_hand_prgression(False, True, 2)
    ohell_game.create_hand_progression()
    ohell_game.active_player = "Joe"

    return ohell_game

def main():
    logging.basicConfig(filename="test_ohell.log",
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
    ohell = init_game(players, "game_state_test")

    ohell.deal(dealer="")
    ohell.deal(dealer="")
    ohell.deal(dealer="")
    ohell.deal(dealer="")
    ohell.deal(dealer="")

    cards_as_str = dict()
    cards_as_str["Joe"] = ['s9', 's10', 's11', 's14', 'h7', 'c8', 'd9']
    cards_as_str["Jack"] = ['s7', 's8', 'h13', 'h11', 'c10', 'd7', 'd13']
    cards_as_str["Jim"] = ['s12', 's13', 'h8', 'h9', 'c12', 'd10', 'd14']
    cards_as_str["Johnny"] = ['h12', 'h14', 'c7', 'c13', 'd8', 'd11', 'd12']

    test_common.create_hands(ohell, cards_as_str)
    ohell.active_player = "Joe"
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

    # state = OhellState("8", "Joe")
    state = ohell.get_state()
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

    # Test Sim Game
    logging.debug("Testing Sim Game")
    game_id = "sim_game"
    ohell = init_game(players, game_id)

    ohell.deal(dealer="")
    ohell.deal(dealer="")
    ohell.deal(dealer="")
    for player in players:
        ohell.place_bet(player, 1)


    # state = OhellState("game_id", "Joe")
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





