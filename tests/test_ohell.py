print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__,__name__,str(__package__)))

from romwhist.ohell.ohell import OhellGame

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
        assert(not ohell.trump_card is None)
        ohell.deal(dealer="")
        ohell.deal(dealer="")
        ohell.deal(dealer="")
        ohell.deal(dealer="")
        assert(ohell.trump_card is None)

        # Testing game play
        for player in players:
                ohell.place_bet(player, 1)

        print ("Playing Hand...")
        for round in range(8):
                print ("    Playing round: " + format(round))
                ohell.create_round()
                active_player = ohell.get_active_player()
                for i in range(len(players)):
                        ohell.card_played(players[i], ohell.get_allowed_cards(players[i])[0])
                print("Winner for round " + format(round) + " is " + ohell.current_round.winning_player)

        ohell.hand_completed()
        scores = ohell.get_scores()
        print("Scores: ")
        for player in players:
                print(player + ": " + format(scores[player]))

        # Test scores
        ohell = OhellGame("Joe", 1, 32)
        for player in players:
                ohell.add_player(player)

        ohell.scores = {"Joe": 1, "Jack": 2, "Jim" : 0, "Johnny" : -1}
        winners = ohell.get_highest_score_player()
        assert (len(winners) == 1)
        assert (winners[0] == "Jack")
        print (winners)

        ohell.scores = {"Joe": 1, "Jack": 2, "Jim" : 0, "Johnny" : 2}
        winners = ohell.get_highest_score_player()
        assert (len(winners) == 2)
        assert (winners[0] == "Jack")
        assert (winners[1] == "Johnny")
        print (winners)
