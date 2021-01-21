import logging
from romwhist.ohell.ohell_ai import OhellAiPlayer
from tests import test_common

if __name__ == '__main__':

    logging.basicConfig(filename='test.log', level=logging.DEBUG)

    ohell_ai = OhellAiPlayer('AI1', '123')
    ohell_ai.game_started(32)
    cards = ["s14", "s10", "d7", "d10", "c9", "c13"]
    ohell_ai.new_hand(cards)
    bet = ohell_ai.player_to_bet([0,1,2,3,4,5,6])
    logging.info("bet = %s", bet)

