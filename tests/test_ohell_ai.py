import logging
from romwhist.ohell.ohell_ai import OhellAiPlayer
from tests import test_common

if __name__ == '__main__':

    logging.basicConfig(filename='test.log', level=logging.DEBUG)

    ohell_ai = OhellAiPlayer('AI1', '1')
    ohell_ai.game_started(32)
    cards = ["s14", "s10", "d7", "d10", "c9", "c13"]
    ohell_ai.new_hand(cards)

    ohell_ai.state.trump = "s"
    ohell_ai.compute_deck_value()

    bet = ohell_ai.player_to_bet([0,1,2,3,4,5,6])
    logging.info("bet = %s", bet)
    #assert bet == 3, bet

    ohell_ai.state.trump = ""
    ohell_ai.compute_deck_value()
    bet = ohell_ai.player_to_bet([0,1,2,3,4,5,6])
    logging.info("bet = %s", bet)
    #assert bet == 2, bet


    #ohell_ai = OhellAiPlayer('AI1', '2')
    #ohell_ai.game_started(32)
    ohell_ai.state.trump = ""
    cards = ["s14", "s10", "d7", "d10", "c9", "c12", "h8", "h13"]
    ohell_ai.new_hand(cards)
    ohell_ai.compute_deck_value()
    bet = ohell_ai.player_to_bet([0,1,2,3,4,5,6])
    logging.info("bet = %s", bet)
    assert bet == 2, bet

    ohell_ai.state.trump = ""
    cards = ["s7", "s10", "d7", "d10", "c9", "c12", "h8", "h12"]
    ohell_ai.new_hand(cards)
    ohell_ai.compute_deck_value()
    bet = ohell_ai.player_to_bet([0,1,2,3,4,5,6])
    logging.info("bet = %s", bet)
    assert bet == 0, bet
