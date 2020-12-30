from enum import Enum
from random import choice
from random import randrange
from ..card import Card
from ..deck import Deck
from ..hand import Hand
from ..round import Round
from ..game import CardGame

class BeloteGame(CardGame):

    class GamePhase(Enum):
        DEAL = "Deal"
        DEAL2 = "Deal2"
        BET = "Bet"
        BET2 = "Bet2"
        PLAY = "Play"

    def __init__(self, game_creator = ""):
        CardGame.__init__(self, game_creator, 0)
        self.taker = None

    def reset(self):
        CardGame.reset(self)
        self.taker = None

    def get_game_phase(self):
        return self._phase

    def add_player(self, player):
        if player in self.players:
            print ("player already exits - re-enabling")
            self._player_status[player] = 1
            # Need to re-start hands
            self.active_player = self.dealer
            self.game_phase = BeloteGame.GamePhase.DEAL
            self.current_round = None
            # self.trump_card = None
            self.bets = dict()
            self.wins = dict()
            self.init_dict(self.bets, "")
            self.init_dict(self.wins, 0)

        else:
            self.players.append(player)
            self._player_status[player] = 1
            self.scores[player] = 0
            self.bets[player] = ""
            self.wins[player] = 0

    def disable_player(self, player):
        print("In Game.disable_player, disabloing playerL " + player)
        if player in self.players:
            self._player_status[player] = 0
            print(self._player_status)
            if player == self.dealer:
                self.dealer = self.next_player_to_deal()
            self.active_player = self.dealer
            self.game_phase = BeloteGame.GamePhase.DEAL
            self.current_round = None
            # self.trump_card = None
            self.bets = dict()
            self.wins = dict()
            self.init_dict(self.bets, -1)
            self.init_dict(self.wins, 0)

    def start_game(self):
        self._started = True;

        # Set deck size based on number of players
        self.deck_size = 32

        # Create hand progression
        self._phase = BeloteGame.GamePhase.BET

    # TODO: should cehck that the bet value is authorized
    def place_bet(self, player, bet):
        print("place_bet for player {} is {}".format(player, bet))
        self.bets[player] = bet

        if (bet == "Pass"):
            # Ask next player
            self.active_player = self.next_player(player)
            if self.next_player_to_bet(player) is None:
                if self._phase == BeloteGame.GamePhase.BET:
                    self._phase = BeloteGame.GamePhase.BET2
                else:
                    # TODO: redistribute cards and reset game
                    self.reset()
                    self._phase = BeloteGame.GamePhase.BET
        else:
            self._phase = BeloteGame.GamePhase.PLAY
            self.trump_suit = bet
            self.taker = player
            # TODO: active player must now be the one after the one that dealt the cards

    # Return None if all players have bet
    def next_player_to_bet(self, player):
        nplayer = self.next_player(player)
        if self.bets[nplayer] != "" or len(self.get_playing_players()) == 1:
            return None
        else:
            return nplayer

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
            # TODO: If player has trump, must play it
            if len(allowed_cards) == 0:
                allowed_cards = self.hands[player].serialize()
        return allowed_cards

    def update_scores(self):
        # TODO: may have to change to playing players only?
        # TODO: count score based on cards in winned rounds
        for p in range(len(self.players)):
            player = self.players[p]

         #self.scoresheet.append([self.bets.copy(), self.wins.copy(), self.scores.copy()])

        return self.scores

    # Iniial deal of 5 card per player
    def deal_1(self, dealer=""):
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()
        self.init_bets()
        self.init_dict(self.wins,0)

        if dealer == "":
            self.dealer = self.active_player
        else:
            self.dealer=dealer

        self.active_player = self.next_player(self.dealer)

        # Create a hand with nb_cards for each player
        for player in self.get_playing_players():
            print (player)
            hand = Hand(self.deck, 5, player)
            self.hands[player] = hand.sort()
            print ("Hand for player ", player, " : ", hand.serialize())

        # Pick up trum card
        self.trump_card = self.deck.deal()

        self._phase = BeloteGame.GamePhase.BET
        return self.hands

    # Distribute 3 cards for each player
    def deal_2(self, dealer=""):
        # Taker takes the trump card then two more, other players take 3 cards
        self.hands[taker].append(self.trump_card)
        for i in range(2):
            self.hands[taker].append(self.self.deck.deal())

        for i in range(3):
            for player in self.get_playing_players():
                if player != self.taker:
                    self.hands[player].append(self.deck.deal())

    # TODO: change this to be based on score reaching a certain threshold
    def is_game_over(self):
        return self._current_hand_nb == len(self._nb_cards_per_hand)


    def init_dict(self, a_dict, value):
        for player in self.players:
            a_dict[player] = value

    def init_bets(self):
        self.init_dict(bets, "")