print('__file__={0:<35} | __name__={1:<20} | __package__={2:<20}'.format(__file__,__name__,str(__package__)))

from romwhist.ohell.ohell import OhellGame

if __name__ == '__main__':
        whist = OhellGame("Joe", 1, 32)
        whist.add_player("Joe")
        whist.add_player("Jack")
        whist.add_player("Jim")
        whist.add_player("Johnny")

        whist.set_hand_prgression()
        whist.create_hand_progression()
        whist.set_hand_prgression(True, True, 1)
        whist.create_hand_progression()
        whist.set_hand_prgression(False, False, 1)
        whist.create_hand_progression()
        whist.set_hand_prgression(False, False, 2)
        whist.create_hand_progression()
        whist.deal(dealer="")
        assert(not whist.trump_card is None)
        whist.deal(dealer="")
        whist.deal(dealer="")
        whist.deal(dealer="")
        whist.deal(dealer="")
        assert(whist.trump_card is None)

        whist = OhellGame("Joe", 1, 32)
        whist.add_player("Joe")
        whist.add_player("Jack")
        whist.add_player("Jim")
        whist.add_player("Johnny")

        whist.scores = {"Joe": 1,"Jack": 2, "Jim" : 2, "Johnny" : -1}
        winners = whist.get_highest_score_player()
        print (winners)
