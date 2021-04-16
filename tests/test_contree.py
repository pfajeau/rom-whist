import logging
from romwhist.contree.contree import ContreeGame
from romwhist.belote.belote import BeloteGame
from romwhist.contree.announce import Announce, ContreStatus

from tests import test_common


def main():
    players = ["Joe", "Jack", "Jim", "Johnny"]
    contree = ContreeGame("Joe")
    for player in players:
        contree.add_player(player)
    assert (len(contree.get_playing_players()) == 4)
    assert contree.bets["Joe"].suit == "", contree.bets["Joe"].suit
    assert contree.bets["Joe"].points == 0, contree.bets["Joe"].points
    contree.start_game()

    contree.deal(dealer="Johnny")
    assert (contree.trump_suit is None)
    assert contree.active_player == "Joe", contree.active_player
    for player in players:
        assert (len(contree.get_hand(player).cards) == 8)

    #self.assertEqual(True, False)

    # Test Place Bet
    assert (len(contree.get_allowed_bets("Joe")[0]) == 5)
    assert (len(contree.get_allowed_bets("Joe")[1]) == len(ContreeGame.all_bet_points))
    bet = Announce("Spade", 80)
    contree.place_bet("Joe", bet)
    assert contree.active_player == "Jack", contree.active_player

    assert (len(contree.get_allowed_bets("Jack")[0]) == 6)
    assert (len(contree.get_allowed_bets("Jack")[1]) == len(ContreeGame.all_bet_points) - 1)
    bet = Announce("Heart", 90)
    contree.place_bet("Jack", bet)
    assert contree.active_player == "Jim", contree.active_player

    assert (len(contree.get_allowed_bets("Jim")[1]) == len(ContreeGame.all_bet_points) - 2)
    bet = Announce("Diamond", "Capot")
    contree.place_bet("Jim", bet)
    assert contree.active_player == "Joe", contree.active_player
    assert contree.phase == BeloteGame.GamePhase.PLAY, contree.phase

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


if __name__ == '__main__':
    logging.basicConfig(filename='test_belote.log',
                        format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s",
                        level=logging.DEBUG)

    main()
