from romwhist.belote.belote import BeloteGame
from romwhist.card import Card

if __name__ == '__main__':
    players = ["Joe", "Jack", "Jim" , "Johnny"]
    belote = BeloteGame("Joe")

    for player in players:
        belote.add_player(player)
    belote.start_game()

    belote.deal_1(dealer="")
    assert (not belote.trump_card is None)

    for player in players:
        assert (len(belote.get_hand(player).cards) == 5)

    belote.place_bet("Joe", Card.SuitName.SPADE)

    belote.deal_2(dealer="")
    for player in players:
        assert (len(belote.get_hand(player).cards) == 8)

    cards_played = belote.get_cards_played()
    assert (cards_played is None)

    # TODO: Simulate a game and check scoring works
    for round in range(8):
        print("Creating new round")
        belote.create_round()
        active_player = belote.get_active_player()
        for i in range(len(players)):
            belote.card_played(players[i], belote.get_allowed_cards(players[i])[0])
        print ("Winner for round " + format(round) + " is " +  belote.current_round.winning_player)
        cards_played = belote.get_cards_played()
        print("Displaying last round cards")
        for player in cards_played:
            print (player + " played: " + str(cards_played[player]))

    belote.hand_completed()
    scores = belote.get_scores()

    print ("Points collected for hand: ")
    for player in players:
        print (player + ": " + format(belote.hand_points[player]))

    print ("Scores: ")
    for player in players:
        print (player + ": " + format(scores[player]))

    # TODO: add tests for 2 and
    #  cards_played = belote.get_cards_played(
    #  for player in cards_played:
    #  print (player + "played: ) + cards_played[player3 players