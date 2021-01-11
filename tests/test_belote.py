from romwhist.belote.belote import BeloteGame

from tests import test_common

if __name__ == '__main__':
    players = ["Joe", "Jack", "Jim", "Johnny"]
    belote = BeloteGame("Joe")

    for player in players:
        belote.add_player(player)
    belote.start_game()

    belote.deal_1(dealer="Johnny")
    assert (belote.trump_card is not None)
    assert (belote.trump_suit is None)
    assert (belote.active_player is "Joe")

    for player in players:
        assert (len(belote.get_hand(player).cards) == 5)

    assert(len(belote.allowed_bets("Joe")) == 2)
    for player in players:
        belote.place_bet(player, "Pass")

    assert (len(belote.allowed_bets("Joe")) == 4)
    belote.place_bet("Joe", "Spade")
    assert (belote.trump_suit == "Spade")

    belote.deal_2(dealer="")
    for player in players:
        assert (len(belote.get_hand(player).cards) == 8)

    cards_played = belote.get_cards_played()
    assert (cards_played is None)

    # Simulate a game and check scoring works
    # First use a pre-defined set of cards for each player
    cards_as_str = dict()
    cards_as_str["Joe"] = ['s9', 's10', 's11', 's13', 'h7', 'h10', 'c8', 'd9']
    cards_as_str["Jack"] = ['s7', 's8', 'h13', 'h11', 'c9', 'c10', 'd7', 'd13']
    cards_as_str["Jim"] = ['s12', 's14', 'h8', 'h9', 'c11', 'c12', 'd10', 'd14']
    cards_as_str["Johnny"] = ['h12', 'h14', 'c7', 'c13', 'c14', 'd8', 'd11', 'd12']

    test_common.create_hands(belote, cards_as_str)
    # Has to set card values (was overwritten by new cards)
    belote.set_cards_rank_and_value()

    belote.active_player = "Joe"
    for i in range(8):
        print("Creating new round")
        a_round = belote.create_round()
        winner = test_common.play_round(belote, a_round)
        assert (belote.belote_announced == BeloteGame.BeloteAnnounced.No)
        assert (belote.belote_state == BeloteGame.BeloteState.Not_Allowed)
        print("Player with belote: " + str(belote.player_with_belote))
        assert (belote.player_with_belote is None)
        print("Winner for round " + str(i) + " is " + belote.current_round.winning_player)

        cards_played = belote.get_cards_played()
        print("Displaying last round cards")
        for player in cards_played:
            print(player + " played: " + str(cards_played[player]))

    belote.hand_completed()
    scores = belote.get_scores()

    print("Points collected for hand: ")
    for player in players:
        print(player + ": " + format(belote.hand_points[player]))

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
    cards_as_str["Jim"] = ['s10', 'h8', 'h9', 'h12', 'c11', 'c12', 'd10', 'd14']
    cards_as_str["Johnny"] = ['s9', 'h14', 'c7', 'c13', 'c14', 'd8', 'd11', 'd12']

    belote.deal_1("")
    belote.place_bet("Joe", "Spade")
    assert (belote.trump_suit == "Spade")
    belote.set_cards_rank_and_value()

    belote.deal_2(dealer="")
    for player in players:
        assert (len(belote.get_hand(player).cards) == 8)

    test_common.create_hands(belote, cards_as_str)
    belote.active_player = "Joe"

    a_round = belote.create_round()
    winner = test_common.play_round(belote, a_round)
    print("Winner for round 1" + " is " + winner)
    assert (winner == "Joe")

    a_round = belote.create_round()
    belote.player_announced_belote("Joe", BeloteGame.BeloteAnnounced.Belote)
    assert (belote.belote_announced == BeloteGame.BeloteAnnounced.Belote)
    winner = test_common.play_round(belote, a_round)
    print("Winner for round 2" + " is " + winner)
    assert (winner == "Joe")
    assert (belote.player_with_belote == "Joe")

    a_round = belote.create_round()
    belote.player_announced_belote("Joe", BeloteGame.BeloteAnnounced.Rebelote)
    assert (belote.belote_announced == BeloteGame.BeloteAnnounced.Rebelote)
    winner = test_common.play_round(belote, a_round)
    print("Winner for round 3" + " is " + winner)
    assert (winner == "Joe")
    assert (belote.player_with_belote == "Joe")
    # TODO: check that Joe's points have increased by 20

    for i in range(5):
        print("Creating new round")
        a_round = belote.create_round()
        winner = test_common.play_round(belote, a_round)
        print("Winner for round " + str(i) + " is " + belote.current_round.winning_player)

        cards_played = belote.get_cards_played()
        print("Displaying last round cards")
        for player in cards_played:
            print(player + " played: " + str(cards_played[player]))

    belote.hand_completed()
    scores = belote.get_scores()

    print("Points collected for hand: ")
    for player in players:
        print(player + ": " + format(belote.hand_points[player]))

    print("Scores: ")
    for player in players:
        print(player + ": " + format(scores[player]))
    # TODO: add tests for 2 and 3 player
