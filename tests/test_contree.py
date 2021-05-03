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
    assert len(contree.get_allowed_bets("Joe")[0]) == 5, len(contree.get_allowed_bets("Joe")[0])
    assert (len(contree.get_allowed_bets("Joe")[1]) == len(ContreeGame.all_bet_points))
    bet = Announce("spade", 80)
    contree.place_bet("Joe", bet)
    assert contree.next_player_to_bet("Joe", "_0") == "Jack", contree.next_player_to_bet("Joe", "_0")
    assert contree.active_player == "Jack", contree.active_player

    assert len(contree.get_allowed_bets("Jack")[0]) == 6, len(contree.get_allowed_bets("Jack")[0])
    assert len(contree.get_allowed_bets("Jack")[1]) == len(ContreeGame.all_bet_points) - 1, len(contree.get_allowed_bets("Jack")[1])
    bet = Announce("heart", 90)
    contree.place_bet("Jack", bet)
    assert contree.active_player == "Jim", contree.active_player

    assert (len(contree.get_allowed_bets("Jim")[0]) == 6)
    assert (len(contree.get_allowed_bets("Jim")[1]) == len(ContreeGame.all_bet_points) - 2)
    bet = Announce("contre", 0)
    contree.place_bet("Jim", bet)
    assert contree.active_player == "Johnny", contree.active_player
    assert contree.phase == BeloteGame.GamePhase.BET, contree.phase

    assert (len(contree.get_allowed_bets("Johnny")[0]) == 2)
    assert contree.get_allowed_bets("Johnny")[0][1] == "surcontre", contree.get_allowed_bets("Johnny")[0][1]
    #assert contree.get_allowed_bets("Johnny")[1][0] == 0, contree.get_allowed_bets("Johnny")[1][0]
    bet = Announce("surcontre", 0)
    contree.place_bet("Johnny", bet)
    assert contree.active_player == "Joe", contree.active_player
    assert contree.phase == BeloteGame.GamePhase.PLAY, contree.phase

    # Test case where player that toook get contred and then passes on his turn
    contree = ContreeGame("Joe")
    for player in players:
        contree.add_player(player)
    contree.start_game()
    contree.deal(dealer="Johnny")
    bet = Announce("spade", 80)
    contree.place_bet("Joe", bet)
    bet = Announce("contre", 0)
    contree.place_bet("Jack", bet)
    bet = Announce("pass", 0)
    contree.place_bet("Jim", bet)
    bet = Announce("pass", 0)
    contree.place_bet("Jim", bet)
    contree.place_bet("Johnny", bet)
    assert contree.active_player == "Joe", contree.active_player
    contree.place_bet("Joe", bet)
    assert contree.phase == BeloteGame.GamePhase.PLAY, contree.phase
    assert contree.bets["Joe"].suit == "pass", contree.bets["Joe"].suit

    # Similar test but Joe surcontre at the end
    contree = ContreeGame("Joe")
    for player in players:
        contree.add_player(player)
    contree.start_game()
    contree.deal(dealer="Johnny")
    bet = Announce("spade", 80)
    contree.place_bet("Joe", bet)
    bet = Announce("contre", 0)
    contree.place_bet("Jack", bet)
    bet = Announce("pass", 0)
    contree.place_bet("Jim", bet)
    bet = Announce("pass", 0)
    contree.place_bet("Jim", bet)
    bet = Announce("pass", 0)
    contree.place_bet("Johnny", bet)
    assert contree.active_player == "Joe", contree.active_player
    bet = Announce("surcontre", 0)
    contree.place_bet("Joe", bet)
    assert contree.phase == BeloteGame.GamePhase.PLAY, contree.phase
    assert contree.bets["Joe"].suit == "surcontre", contree.bets["Joe"].suit



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
