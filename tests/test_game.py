import pytest
from game import RomWhistGame

if __name__ == '__main__':
        whist = RomWhistGame("Joe", 1, 32)
        whist.add_player("Joe")
        whist.add_player("Jack")
        whist.add_player("Jim")
        whist.add_player("Johnny")

        whist.set_hand_prgression()
        whist.set_hand_prgression(True, True, 1)
        whist.set_hand_prgression(False, False, 1)
        whist.set_hand_prgression(False, False, 2)
        whist.deal(dealer="")
        assert(not whist.trump_card is None)
        whist.deal(dealer="")
        whist.deal(dealer="")
        whist.deal(dealer="")
        whist.deal(dealer="")
        assert(whist.trump_card is None)

        whist = RomWhistGame("Joe", 1, 32)
        whist.add_player("Joe")
        whist.add_player("Jack")
        whist.add_player("Jim")
        whist.add_player("Johnny")
        whist.deal(5)
        assert(whist.deal(20) is None)
        assert(whist.deal(8, with_trump=True) is None)
