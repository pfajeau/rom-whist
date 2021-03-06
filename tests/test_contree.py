import logging
from romwhist.contree.contree import ContreeGame


def main():
    players = ["Joe", "Jack", "Jim", "Johnny"]
    contree = ContreeGame("Joe")
    for player in players:
        contree.add_player(player)
    assert (len(contree.get_playing_players()) == 4)
    contree.start_game()

    contree.deal(dealer="Johnny")
    assert (contree.trump_suit is None)
    assert contree.active_player == "Joe", contree.active_player
    for player in players:
        assert (len(contree.get_hand(player).cards) == 8)

    #self.assertEqual(True, False)

    # Test Place Bet
    assert (len(contree.get_allowed_bets("Joe")) == len(ContreeGame.all_bet_points))
    bet = ContreeGame.Announce("Spade", 80)
    contree.place_bet("Joe", bet)
    assert contree.active_player == "Jack", contree.active_player



if __name__ == '__main__':
    logging.basicConfig(filename='test_belote.log',
                        format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s",
                        level=logging.DEBUG)

    main()
