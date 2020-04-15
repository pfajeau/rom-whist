from Card import Card
from Deck import *
from random import choice
from random import randrange
from Hand import Hand

class RomWhistGame():

    def __init__(self, game_creator = ""):
        players = []
        scores = dict()
        current_round = 0

    def add_player(player):
        player.append(player)

    def get_players():
        return get_players

    def start_game():
        # create deck
        # give a card to each player
        # show trump
        # signal to player when it is their return

        pass

    def new_hand(nb_cards):
        # Create a hand with nb_cards for each player

    def end_game():
        pass


def main():
    D = Deck(); #create a deck of 52 cards
    D.shuffle()

    rank = randrange(1,14)
    suit = choice(Card.SUITS)
    myCard = Card(rank, suit)
    index = Card.SUITS.index(suit)
    suitN = Card.SUIT_NAMES[index]

    print("\nThe card is:", myCard, "and the trump suit is:",suitN,"\n")

    #outputs trump suit and card

    PN = 0
    PS = 0
    n = Hand("North")
    s = Hand("South")

    for numbers in range(1,27):
        TN = D.deal()
        print("round:", numbers,)
        TS = D.deal()
        print(TN)
        print(TS)

        #if both are prime suits
        if ((TN.suit() == TS.suit()) and (TN.suit() == suit)):
            if TN.rank() > TS.rank():
                print("North won this round\n")
                n.add(TN)
                n.add(TS)
                PN+=1
            else:
                print("South won this round\n")
                s.add(TS)
                s.add(TS)
                PS+=1

        #if they are not the same suit and neither is the prime suit
        elif ((TN.suit() != TS.suit()) and (TN.suit() != suit) and (TS.suit() != suit)):
            print("Cards are discarded")

        elif (TN.suit() == suit and TS.suit() != suit):
            print("North won this round\n")
            n.add(TN)
            n.add(TS)
            PN+=1

        elif (TN.suit != suit and TS.suit() == suit):
            print("South won this round\n")
            s.add(TS)
            s.add(TS)
            PS+=1

        #if they are same suit but not prime suit
        elif(TN.suit() == TS.suit() and TN.suit() != suit):
            if TN.rank() > TS.rank():
                print("North won this round\n")
                n.add(TN)
                n.add(TS)
                PN+=1
            elif TS.rank() > TN.rank():
                print("South won this round\n")
                s.add(TS)
                s.add(TS)
                PS+=1

        else:
            print("Needs to be programmed\n")

    print("North player has ",PN," points")
    print("South player has ",PS," points")

    if(PN > PS):
        print("\nNorth Wins")
    elif(PS > PN):
        print("\nSouth Wins")
    elif(PN == PS):
        print("Nobody wins, it's a tie")
