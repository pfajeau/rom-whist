from enum import Enum
from random import choice
from random import randrange
from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.hand import Hand
from romwhist.round import Round

class RomWhistGame():

    MANUAL_DEALING = "manual"
    AUTOMATED_DEALING = "automated"

    class GamePhase(Enum):
        DEAL = "Deal"
        BET = "Bet"
        PLAY = "Play"

    def __init__(self, game_creator = "", bonus_win = 1, deck_size=0):
        self.players = []
        self.current_round = None
        self.trump_card = None
        self.hands=dict()
        self.scores=dict()
        self.bets=dict()
        self.wins=dict()
        self.bonus_win = bonus_win
        self.dealer = None
        self.init_dict(self.scores,0)
        self.dealing_method = RomWhistGame.MANUAL_DEALING
        self.owner = game_creator
        self.active_player = self.owner
        self.deck_size = deck_size
        self._nb_cards_per_hand=None
        self._current_hand_nb = 0
        self._start_of_no_trump = 0
        self._multiple_one_card = False
        self._multiple_no_trump = True
        self._increment = 1
        self._started = False;
        self._phase = RomWhistGame.GamePhase.DEAL
        self.scoresheet=[]
        self._player_status=dict()
        self.init_dict(self._player_status, 1)

    def reset(self):
        self.current_round = None
        self.trump_card = None
        self.hands=dict()
        self.scores=dict()
        self.bets=dict()
        self.wins=dict()
        self.dealer = None
        self.init_dict(self.scores,0)
        self.active_player = self.owner
        self.init_dict(self.bets, -1)
        self.init_dict(self.wins, 0)
        self._current_hand_nb = 0

    def get_game_phase(self):
        return self._phase

    # Define the card distribution pattern
    def set_hand_prgression(self, multiple_one_card=False, multiple_no_trump=True, increment=1):
        self.dealing_method = RomWhistGame.AUTOMATED_DEALING
        self._multiple_one_card = multiple_one_card
        self._multiple_no_trump = multiple_no_trump
        self._increment = increment

    def create_hand_progression(self):
        # Create list of hands to plays
        self._nb_cards_per_hand=[]

        # Note: the following assumes that the list is ordered which is only
        # guaranteed with python3
        # Start with the one card hands
        if self._multiple_one_card:
            for i in range(0, len(self.get_playing_players())):
                self._nb_cards_per_hand.append(1)
        else:
            self._nb_cards_per_hand.append(1)

        # Max number of card per players
        max_cards = int(self.deck_size / len(self.get_playing_players()))

        for i in range(1+self._increment, max_cards, self._increment):
            self._nb_cards_per_hand.append(i)

        end_of_climb = len(self._nb_cards_per_hand)
        self._start_of_no_trump = len(self._nb_cards_per_hand)
        # Now the no trump _hands
        if self._multiple_no_trump:
            for i in range(0, len(self.get_playing_players())):
                self._nb_cards_per_hand.append(max_cards)
        else:
            self._nb_cards_per_hand.append(max_cards)

        self._end_of_no_trump = len(self._nb_cards_per_hand)-1

        # Now the downhill
        for i in range(1,end_of_climb+1):
            self._nb_cards_per_hand.append(self._nb_cards_per_hand[end_of_climb-i])

        print ("Distribution of cards: ", self._nb_cards_per_hand)
        print ("Index start of no trump: ", self._start_of_no_trump)
        print ("Index end of no trump: ", self._end_of_no_trump)

    def get_active_player(self):
        return self.active_player;

    def set_owner(self, player):
        self.owner = player

    def get_owner(self):
        return self.owner

    def game_started(self):
        return self._started;

    # Return a list of players with the mazimum score
    def get_highest_score_player(self):
        maximum = max(self.scores.values())
        winners = []
        for player in self.scores:
            if self.scores[player] == maximum:
                winners.append(player)

        # result = filter(lambda x:x[1] == maximum,self.scores.items())
        # for player in result:
        #     winners.append(player[0])

        return winners

    def add_player(self, player):
        if player in self.players:
            print ("player already exits - re-enabling")
            self._player_status[player] = 1
            # Need to re-start hands
            self.active_player = self.dealer
            self.game_phase = RomWhistGame.GamePhase.DEAL
            self.current_round = None
            # self.trump_card = None
            self.bets = dict()
            self.wins = dict()
            self.init_dict(self.bets, -1)
            self.init_dict(self.wins, 0)

        else:
            self.players.append(player)
            self._player_status[player] = 1
            self.scores[player] = 0
            self.bets[player] = -1
            self.wins[player] = 0

    def disable_player(self, player):
        print("In Game.disable_player, disabloing playerL " + player)
        if player in self.players:
            self._player_status[player] = 0
            print(self._player_status)
            if player == self.dealer:
                self.dealer = self.next_player_to_deal()
            self.active_player = self.dealer
            self.game_phase = RomWhistGame.GamePhase.DEAL
            self.current_round = None
            # self.trump_card = None
            self.bets = dict()
            self.wins = dict()
            self.init_dict(self.bets, -1)
            self.init_dict(self.wins, 0)


    def remove_player(self, player):
        self.disable_player(player)
        self.players.remove(player)

    def get_players(self):
        return self.players

    def get_playing_players(self):
        # TODO: could probably do that with a filter in one line of code
        playing_players = []
        for player in self.players:
            if self._player_status[player] == 1:
                playing_players.append(player)
        return playing_players

    def start_game(self):
        self._started = True;
        self._current_hand_nb = 0

        # Set deck size based on number of players
        self.deck_size = len(self.players) * 8

        # Create hand progression
        if self.dealing_method == RomWhistGame.AUTOMATED_DEALING:
            self._phase = RomWhistGame.GamePhase.BET
            self.create_hand_progression()
        else:
            self._phase = RomWhistGame.GamePhase.DEAL

    def get_hand(self, player):
        return self.hands[player]

    def get_hands(self):
        return self.hands

    def get_bets(self):
        return self.bets

    def get_wins(self):
        return self.wins;

    def is_hand_completed(self):
        for player in self.get_playing_players():
            if len(self.hands[player].get_cards()) > 0:
                return False
        return True

    def create_round(self):
        if self.trump_card is None:
            suit = None
        else:
            suit = self.trump_card.suit()
        self.current_round = Round(self.get_playing_players(), suit)
        return self.current_round

    # TODO: should cehck that the bet value is authorized
    def place_bet(self, player, bet):
        print("place_bet for player {} is {}".format(player, bet))
        self.bets[player] = bet
        self.active_player = self.next_player(player)
        if self.next_player_to_bet(player) is None:
            self._phase = RomWhistGame.GamePhase.PLAY


    def sum_bets_placed(self):
        bets_placed = 0
        for player in self.bets:
            bets_placed = bets_placed + max(self.bets[player], 0)
            print("sum bet placed: ", bets_placed)
        return bets_placed

    def forbidden_bet(self, player):
        if self.hands.get(player) is None:
            return -1   # No hand yet
        if self.next_player_to_bet(player) is None:
            return len(self.hands[player].get_cards()) - self.sum_bets_placed()
        else:
            return -1

    def allowed_bets(self, player):
        if self.hands.get(player) is None:
            return []   # No hand yet
        allowed_bets = list(range(len(self.get_hand(player).get_cards())+1))
        print("allowed bets:", allowed_bets)
        if self.next_player_to_bet(player) is None:
            forbidden_bet = self.forbidden_bet(player)
            if (forbidden_bet >= 0):
                print("forbidden bet:", forbidden_bet)
                allowed_bets.remove(forbidden_bet)
        return allowed_bets

    # Return None if all players have bet
    def next_player_to_bet(self, player):
        nplayer = self.next_player(player)
        if self.bets[nplayer] != -1 or len(self.get_playing_players()) == 1:
            return None
        else:
            return nplayer

    def next_player_to_deal(self):
        nplayer = self.next_player(self.dealer)
        return nplayer

    # Return round winner if last card played None otherwise
    def card_played(self, player, trump_card_value):
        # Remove card from player hands
        card = Card.card_from_value(trump_card_value)
        self.hands[player].remove(card)
        self.current_round.card_played(player, card)
        if self.current_round.last_card_played():
            winner = self.current_round.compute_winner()
            self.wins[winner] = self.wins[winner] + 1
            print("in card_played, wins for player {} is {}".format(player, self.wins[player]))
            if self.is_hand_completed():
                self.active_player = self.next_player_to_deal()
            else:
                self.active_player = winner
            return winner
        else:
            self.active_player = self.next_player(player)
            return None

    # Return list of allowed cards as a list of
    # cards represented as string (e.g. 'c4')
    def get_allowed_cards(self, player):
        # Allowed cards are cars of the same suit than the first card played
        # If no cards are of the same suit, any card is allowed_cards
        allowed_cards = []
        if self.current_round is None:
            return allowed_cards
        if self.current_round.get_first_card_played() is None:
            # Round is just starting, all cards are allowed
            allowed_cards = self.get_hand(player).serialize()
        else:
            for card in self.hands[player].get_cards():
                if card.suit() == self.current_round.get_first_card_played().suit():
                    allowed_cards.append(str(card))
            if len(allowed_cards) == 0:
                allowed_cards = self.hands[player].serialize()
        return allowed_cards

    def get_current_round(self):
        return self.current_round

    def update_scores(self):
        # TODO: may have to change to playing players only?
        for p in range(len(self.players)):
            player = self.players[p]
            print ("Player bet: {} - PLayer wins: {}".format(self.bets[player], self.wins[player]))
            if self.bets[player] == -1:
                # Do nothing, means player is not playing
                self.scores[player] = self.scores[player]
            elif self.bets[player] == self.wins[player]:
                self.scores[player] = self.scores[player] + self.bonus_win + self.wins[player]
            else:
                self.scores[player] = self.scores[player] - \
                abs(self.wins[player] - self.bets[player])
        self.scoresheet.append([self.bets.copy(), self.wins.copy(), self.scores.copy()])

        return self.scores

    def get_scores(self):
        return self.scores

    def all_rounds_played(self):
        return self.current_round.last_card_played()

    def deal(self, nb_cards=0, with_trump=False, dealer=""):
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()
        self.init_dict(self.bets,-1)
        self.init_dict(self.wins,0)

        if dealer == "":
            self.dealer = self.active_player
        else:
            self.dealer=dealer

        self.active_player = self.next_player(self.dealer)

        # If automated dealing set cards to deal
        if self.dealing_method == RomWhistGame.AUTOMATED_DEALING:
            print ("current_hand_nb: ", self._current_hand_nb)
            cards_to_deal = self._nb_cards_per_hand[self._current_hand_nb]
            if cards_to_deal is None:
                cards_to_deal = 0
        else:
            cards_to_deal = nb_cards;

        if cards_to_deal <= 0 or cards_to_deal > self.deck.size() / len(self.get_playing_players()):
            return None
        else:
            # Create a hand with nb_cards for each player
            for player in self.get_playing_players():
                print (player)
                hand = Hand(self.deck, cards_to_deal, player)
                self.hands[player] = hand.sort()
                print ("Hand for player ", player, " : ", hand.serialize())

            deal_trump = with_trump

            # Check whether play is with or without trump in case of automated dealing
            if self.dealing_method == RomWhistGame.AUTOMATED_DEALING:
                if self._current_hand_nb < self._start_of_no_trump or self._current_hand_nb > self._end_of_no_trump:
                    deal_trump = True
                else:
                    deal_trump = False

            print ("Trump: ", deal_trump)
            # Pick up trum card
            if deal_trump:
                trump_card = self.deck.deal()
                if trump_card is None:
                    # Case where all cards have been dealt
                    # and no more card available to be the trump card
                    # TODO: WOuld be best to raise an excepiton
                    return None
                else:
                    self.trump_card = trump_card
            else:
                self.trump_card = None

            self._current_hand_nb = self._current_hand_nb+1
            self._phase = RomWhistGame.GamePhase.BET
            return self.hands

    # TODO
    def get_nb_cards_to_deal(self):
        return 0

    # TODO
    def get_play_with_trump(self):
        return True

    def is_game_over(self):
        if self.dealing_method == RomWhistGame.AUTOMATED_DEALING:
            return self._current_hand_nb == len(self._nb_cards_per_hand)
        else:
            return False

    def next_player(self, player):
        pos = self.players.index(player)
        if pos == len(self.players)-1:
            next_player = self.players[0]
        else:
            next_player = self.players[pos+1]

        if  self._player_status[next_player] == 1:
            return next_player
        else:
            return self.next_player(next_player)

    def init_dict(self, a_dict, value):
        for player in self.players:
            a_dict[player] = value


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
