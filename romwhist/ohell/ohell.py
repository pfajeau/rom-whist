from romwhist.game import CardGame
from romwhist.deck import Deck
from romwhist.card import Card
from romwhist.hand import Hand
from romwhist.round import Round


class OhellGame(CardGame):


    def __init__(self, game_creator = "", bonus_win = 1, deck_size=0, id=0):
        CardGame.__init__(self, game_creator, deck_size, id)
        self.bonus_win = bonus_win
        self._start_of_no_trump = 0
        self._multiple_one_card = False
        self._multiple_no_trump = True
        self._increment = 1
        self._nb_cards_per_hand = None

    def reset(self):
        CardGame.reset(self)

    # Define the card distribution pattern
    def set_hand_prgression(self, multiple_one_card=False, multiple_no_trump=True, increment=1):
        self.dealing_method = CardGame.AUTOMATED_DEALING
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

    # TODO: should cehck that the bet value is authorized
    def place_bet(self, player, bet):
        print("place_bet for player {} is {}".format(player, bet))
        self.bets[player] = bet
        self.active_player = self.next_player(player)
        if self.next_player_to_bet(player) is None:
            self.phase = CardGame.GamePhase.PLAY

    def sum_bets_placed(self):
        bets_placed = 0
        for player in self.bets:
            bets_placed = bets_placed + max(self.bets[player], 0)
            print("sum bet placed: ", bets_placed)
        return bets_placed

    def forbidden_bet(self, player):
        if self.hands.get(player) is None:
            return -1  # No hand yet
        if self.next_player_to_bet(player) is None:
            return len(self.hands[player].get_cards()) - self.sum_bets_placed()
        else:
            return -1

    def allowed_bets(self, player):
        if self.hands.get(player) is None:
            return []  # No hand yet
        allowed_bets = list(range(len(self.get_hand(player).get_cards()) + 1))
        print("allowed bets:", allowed_bets)
        if self.next_player_to_bet(player) is None:
            forbidden_bet = self.forbidden_bet(player)
            if (forbidden_bet >= 0):
                print("forbidden bet:", forbidden_bet)
                allowed_bets.remove(forbidden_bet)
        return allowed_bets

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
                if card.get_suit() == self.current_round.get_first_card_played().get_suit():
                    allowed_cards.append(str(card))
            if len(allowed_cards) == 0:
                allowed_cards = self.hands[player].serialize()
        return allowed_cards


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
        if self.dealing_method == CardGame.AUTOMATED_DEALING:
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
            if self.dealing_method == CardGame.AUTOMATED_DEALING:
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
                    self.trump_suit = trump_card.get_suit_name()

            else:
                self.trump_card = None
                self.trump_suit = None

            self._current_hand_nb = self._current_hand_nb+1
            self.phase = CardGame.GamePhase.BET
            return self.hands

    def is_game_over(self):
        if self.dealing_method == CardGame.AUTOMATED_DEALING:
            return self._current_hand_nb == len(self._nb_cards_per_hand)
        else:
            return False

# TODO: Move anything specific to OhHell to this class from CardGame