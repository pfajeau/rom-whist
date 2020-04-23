from .card import Card
from .deck import Deck
from random import choice
from random import randrange
from .hand import Hand
from .round import Round

deck = None
hands = dict()

class RomWhistGame():

    def __init__(self, game_creator = ""):
        self.players = []
        scores = dict()
        self.current_round = None
        self.trump_card = None
        self.deck = Deck()
        self.hands=dict()

    def add_player(self, player):
        self.players.append(player)

    def remove_player(self, player):
        self.players.remove(player)

    def get_players(self):
        return self.players

    def start_game(self):
        # create deck
        pass

    def get_hands(self):
        return self.hands

    def create_round(self):
        if self.trump_card is None:
            suit = None
        else:
            suit = self.trump_card.suit()
        self.current_round = Round(self.players, suit)
        return self.current_round

    def card_played(self, player, trump_card_value):
        # Remove card from player hands
        card = Card.card_from_value(trump_card_value)
        self.hands[player].remove(card)
        self.current_round.card_played(player, card)

    def get_current_round(self):
        return self.current_round

    def create_hands(self, nb_cards, with_trump=False):
        self.deck.shuffle()
        # Create a hand with nb_cards for each player
        for p in range(len(self.players)):
            print (self.players[p])
            print ("Nb cards:", nb_cards)
            hand = Hand(self.deck, nb_cards, self.players[p])
            self.hands[self.players[p]] = hand
            # hand.dump()

        # Pick up trum cards
        if with_trump:
            self.trump_card = self.deck.deal()

        return self.hands

    def end_game(self):
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
