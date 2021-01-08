from romwhist.belote.belote import BeloteGame
from romwhist.card import Card
from romwhist.hand import Hand


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

    belote.place_bet("Joe", "Spade")
    assert(belote.trump_suit == "Spade")

    belote.deal_2(dealer="")
    for player in players:
        assert (len(belote.get_hand(player).cards) == 8)

    cards_played = belote.get_cards_played()
    assert (cards_played is None)

    # TODO: Simulate a game and check scoring works
    # First use a pre-defined set of cards for each player
    cards_as_str = dict()
    cards_as_str["Joe"] =  ['s9', 's10', 's11', 's14', 'h7','h10', 'c8', 'd9']
    cards_as_str["Jack"] = ['s7', 's8', 'h13', 'h11', 'c9', 'c10', 'd7', 'd13']
    cards_as_str["Jim"] =  ['s12', 's13', 'h8', 'h9', 'c11', 'c12', 'd10', 'd14']
    cards_as_str["Johnny"] = ['h12', 'h14', 'c7', 'c13', 'c14', 'd8', 'd11', 'd12']

    cards = dict()
    for player in players:
        hand = Hand(belote.deck, 0)
        for card_as_str in cards_as_str[player]:
            hand.add(Card.card_from_value(card_as_str))
        belote.hands[player] = hand
        print("Hand for player " + player + ": " + str(belote.hands[player].serialize()))

    for game_round in range(8):
        print("Creating new round")
        belote.create_round()
        active_player = belote.get_active_player()
        for i in range(len(players)):
            print ("Allowed cards for " + players[i] + " : {}".format(belote.get_allowed_cards(players[i])))
            belote.card_played(players[i], belote.get_allowed_cards(players[i])[0])
        print ("Winner for round " + format(game_round) + " is " + belote.current_round.winning_player)
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