print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__, __name__, str(__package__)))

from romwhist.ohell.ohell import OhellGame
from tests import test_common

if __name__ == '__main__':
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

    cards_played = ohell.get_cards_played()
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

    print("Playing Hand...")
    for i in range(8):
        print("    Playing round: " + str(i))
        round = ohell.create_round()
        winner = test_common.play_round(ohell, round)
        print("Winner for round " + str(i) + " is " + ohell.current_round.winning_player)

        cards_played = ohell.get_cards_played()
        print("Displaying last round cards")
        for player in cards_played:
                print(player + " played: " + str(cards_played[player]))

    ohell.hand_completed()
    scores = ohell.get_scores()
    print("Scores: ")
    for player in players:
        print(player + ": " + format(scores[player]))

    # Test scores
    ohell = OhellGame("Joe", 1, 32)
    for player in players:
        ohell.add_player(player)

    ohell.scores = {"Joe": 1, "Jack": 2, "Jim": 0, "Johnny": -1}
    winners = ohell.get_highest_score_player()
    assert (len(winners) == 1)
    assert (winners[0] == "Jack")
    print(winners)

    ohell.scores = {"Joe": 1, "Jack": 2, "Jim": 0, "Johnny": 2}
    winners = ohell.get_highest_score_player()
    assert (len(winners) == 2)
    assert (winners[0] == "Jack")
    assert (winners[1] == "Johnny")
    print(winners)
