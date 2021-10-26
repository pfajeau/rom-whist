import logging
from romwhist.belote.belote import BeloteGame
from romwhist.belote.belote_status import BeloteStatus
from romwhist.player import Player

from tests import test_common


def main():
    logging.basicConfig(filename='test_belote.log',
                        format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s",
                        level=logging.DEBUG)

    player_names = ["Joe", "Jack", "Jim", "Johnny"]
    players_by_name = dict()
    players = []
    belote = BeloteGame("Joe")

    for player_name in player_names:
        player = belote.add_player(player_name,
                          Player.PlayerType.HUMAN,
                          Player.PlayerStatus.ACTIVE)
        players_by_name[player_name] = player
        players.append(player)

    Joe = players_by_name["Joe"]
    Jack = players_by_name["Jack"]
    Jim = players_by_name["Jim"]
    Johnny = players_by_name["Johnny"]

    assert(len(belote.get_playing_players()) == 4)
    belote.start_game()

    belote.deal(dealer=players_by_name["Johnny"])
    assert (belote.trump_card is not None)
    assert (belote.trump_suit is None)
    assert (belote.active_player is players_by_name["Joe"])

    for player in players:
        assert (len(belote.get_hand(player).cards) == 5)

    assert(len(belote.get_allowed_bets(players_by_name["Joe"])) == 2)
    for player in players:
        belote.place_bet(player, "pass")

    assert (len(belote.get_allowed_bets(players_by_name["Joe"])) == 4)
    belote.place_bet(players_by_name["Joe"], "spade")
    assert (belote.trump_suit == "spade")

    belote.deal_2(dealer=None)
    for player in players:
        assert (len(belote.get_hand(player).cards) == 8)

    cards_played = belote.get_cards_played_current_round()
    assert (cards_played is None)

    # Simulate a game and check scoring works
    # First use a pre-defined set of cards for each player
    cards_as_str = dict()
    cards_as_str["Joe"] = ['s9', 's10', 's11', 's13', 'h7', 'h10', 'c8', 'd9']
    cards_as_str["Jack"] = ['s7', 's14', 'h13', 'h11', 'c9', 'c10', 'd7', 'd13']
    cards_as_str["Jim"] = ['s12', 's8', 'h8', 'h9', 'c11', 'c12', 'd10', 'd14']
    cards_as_str["Johnny"] = ['h12', 'h14', 'c7', 'c13', 'c14', 'd8', 'd11', 'd12']

    test_common.create_hands(belote, cards_as_str)

    # Set card values (were overwritten by new cards since they are different objects)
    belote.set_cards_rank_and_value()

    # Force belote/rebelote to Not Allowed, otherwise tests may fail occasionally
    belote.belote_status = BeloteStatus.Not_Allowed
    belote.player_with_belote = None
    a_round = belote.create_round()

    belote.active_player = players_by_name["Joe"]
    belote.play_card(belote.active_player, "s10")
    allowed_cards = belote.get_allowed_cards(Jack)
    print("Allowed card for Jack: " + str(allowed_cards))
    assert(allowed_cards.index("s14") != -1)
    assert(len(allowed_cards) == 1)

    belote.play_card(belote.active_player, "s14")
    allowed_cards = belote.get_allowed_cards(players_by_name["Jim"])

    belote.play_card(belote.active_player, "s8")
    allowed_cards = belote.get_allowed_cards(players_by_name["Johnny"])
    assert(len(allowed_cards) == 8)
    belote.play_card(belote.active_player, "c7")

    print("Winner for round 1 is " + belote.current_round.winning_player)

    for i in range(2, 9):
        print("Creating new round")
        a_round = belote.create_round()
        test_common.play_round(belote, a_round)
        assert belote.belote_status == BeloteStatus.Not_Allowed, belote.belote_status
        print("Player with belote: " + str(belote.player_with_belote))
        assert (belote.player_with_belote is None)
        print("Winner for round " + str(i) + " is " + belote.current_round.winning_player)

        cards_played = belote.get_cards_played_current_round()
        print("Displaying last round cards")
        for player in cards_played:
            print(player + " played: " + str(cards_played[player]))

    belote.hand_completed()
    scores = belote.get_scores()

    total_points = 0
    print("Points collected for hand: ")
    for player in players:
        print(player + ": " + format(belote.hand_points[player]))

    total_points = belote.hand_points[Joe] + belote.hand_points[Jack]
    assert total_points == BeloteGame.TOTAL_POINTS, total_points

    print("Scores: ")
    for player in players:
        print(player + ": " + format(scores[player]))

    # Test belote / rebelote
    # Simulate a game and check scoring works
    # First use a pre-defined set of cards for each player
    print("Testing Belote/Rebelote")
    cards_as_str = dict()
    cards_as_str["Joe"] = ['s11', 's13', 's12', 's14', 'h7', 'h10', 'c8', 'd9']
    cards_as_str["Jack"] = ['s7', 's8', 'h13', 'h11', 'c9', 'c10', 'd7', 'd13']
    cards_as_str["Jim"] = ['s10', 'c11', 'c12', 'c13', 'd8', 'd10', 'd11', 'd14']
    cards_as_str["Johnny"] = ['s9', 'h8', 'h9', 'h12', 'h14', 'c7', 'c14', 'd12']

    belote.deal(None)
    for player in players:
        assert (len(belote.get_hand(player).cards) == 5)

    # Override cards with pre-defined set
    test_common.create_hands(belote, cards_as_str)
    belote.place_bet(Joe, "spade")
    assert (belote.trump_suit == "spade")

    belote.deal_2(dealer="")
    assert belote.belote_status == BeloteStatus.Allowed, belote.belote_status.name
    assert belote.player_with_belote == Joe

    # Override cards with pre-defined set
    test_common.create_hands(belote, cards_as_str)
    for player in players:
        assert (len(belote.get_hand(player).cards) == 8)

    test_common.create_hands(belote, cards_as_str)
    belote.place_bet(Joe, "spade")
    belote.active_player = Joe
    assert(belote.has_player_card(Joe, "s12") is True)
    assert(belote.has_player_card(Joe, "s13") is True)
    assert belote.belote_status == BeloteStatus.Allowed, belote.belote_status.name
    assert(belote.player_with_belote == Joe)

    # First round
    a_round = belote.create_round()
    belote.active_player = Joe
    belote.player_announced_belote(Joe, BeloteGame.BeloteAnnounced.BELOTE)
    print("Belote status is: ")
    print(belote.belote_status)
    assert (belote.belote_status == BeloteStatus.Belote_Announced)
    winner = test_common.play_round(belote, a_round, "s12")
    assert belote.belote_status == BeloteStatus.Belote_Played, belote.belote_status
    print("Winner for round 1" + " is " + winner)
    assert (winner == Johnny)
    assert (belote.player_with_belote == Joe)

    # Second round
    a_round = belote.create_round()
    belote.active_player = Joe
    belote.player_announced_belote(Joe, BeloteGame.BeloteAnnounced.REBELOTE)
    assert (belote.belote_status == BeloteStatus.Rebelote_Announced)
    winner = test_common.play_round(belote, a_round, "s13")
    assert (belote.belote_status == BeloteStatus.Rebelote_Played)
    print("Winner for round 2" + " is " + winner)
    assert (winner == Joe)
    assert (belote.player_with_belote == Joe)
    # TODO: check that Joe's points have increased by 20

    # Third round: test that player can "piss"
    a_round = belote.create_round()
    belote.active_player = Joe
    belote.play_card(Joe, 'h10')
    belote.play_card(Jack, 'h13')
    allowed_cards = belote.get_allowed_cards(Jim)
    print("ALlowed cards for Jim: " + str(allowed_cards))
    assert len(allowed_cards) == 6, len(allowed_cards)
    belote.play_card(Jim, 'c12')
    belote.play_card(Johnny, 'h14')
    winner = a_round.winning_player
    print("Winner for round 3" + " is " + winner)
    assert winner == Johnny, winner

    for i in range(4, 9):
        print("Creating new round")
        a_round = belote.create_round()
        winner = test_common.play_round(belote, a_round)
        print("Winner for round " + str(i) + " is " + belote.current_round.winning_player)

        cards_played = belote.get_cards_played_current_round()
        print("Displaying last round cards")
        for player in cards_played:
            print(player + " played: " + str(cards_played[player]))

#    state = BeloteState("8")
    state = belote.get_state()
    logging.debug("State: " + repr(state))
    belote.set_state(state)

    belote.hand_completed()
    scores = belote.get_scores()

    print("Points collected for hand: ")
    for player in players:
        print(player + ": " + format(belote.hand_points[player]))

    total_points = belote.hand_points[Joe] + belote.hand_points[Jack]
    assert total_points == belote.TOTAL_POINTS + belote.BELOTE_REBELOTE, total_points

    print("Scores: ")
    for player in players:
        print(player + ": " + format(scores[player]))

    print("Testing all players passing twice")
    belote.deal(None)
    for player in players:
        assert (len(belote.get_hand(player).cards) == 5)

    belote.active_player = Joe
    for player in players:
        belote.place_bet(player, "pass")

    for player in players:
        belote.place_bet(player, "pass")

    # New hands should have been distributed
    print("Active player is: " + belote.active_player)
    # TODO: add tests for 2 and 3 player


if __name__ == '__main__':
    main()
