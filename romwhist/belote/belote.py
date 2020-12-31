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
        self.teams = []
        self.hand_points=dict()   # The number of points collected while the hand is played
        self.init_dict(self.hand_points,0)

        # Points and ranks will change for the trump suit once it is known
        self.card_points={"c7": 0, "c8":0, "c9":0, "c10":10, "c11":2, "c12":3, "c13":4, "c14":11,
                          "d7": 0, "d8":0, "d9":0, "d10":10, "d11":2, "d12":3, "d13":4, "d14":11,
                          "h7": 0, "h8": 0, "h9": 0, "h10": 10, "h11": 2, "h12": 3, "h13": 4, "h14": 11,
                          "s7": 0, "s8": 0, "s9": 0, "s10": 10, "s11": 2, "s12": 3, "s13": 4, "s14": 11}

        self.card_ranks={"c7": 7, "c8": 8, "c9": 9, "c10": 14, "c11": 11, "c12": 12, "c13": 13, "c14": 15,
                         "d7": 7, "d8": 8, "d9": 9, "d10": 14, "d11": 11, "d12": 12, "d13": 13, "d14": 15,
                         "h7": 7, "h8": 8, "h9": 9, "h10": 14, "h11": 11, "h12": 12, "h13": 13, "h14": 15,
                         "s7": 7, "s8": 8, "s9": 9, "s10": 14, "s11": 11, "s12": 12, "s13": 14, "s14": 15}


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
            self.hand_points[player] = 0

        else:
            self.players.append(player)
            self._player_status[player] = 1
            self.scores[player] = 0
            self.bets[player] = ""
            self.wins[player] = 0
            self.hand_points[player] = 0

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

    def place_bet(self, player, bet):
        print("place_bet for player {} is {}".format(player, bet))
        self.bets[player] = bet

        if (bet == "Pass"):
            print ("Player passed")
            # Ask next player
            self.active_player = self.next_player(player)
            if self.next_player_to_bet(player) is None:
                if self._phase == BeloteGame.GamePhase.BET:
                    self._phase = BeloteGame.GamePhase.BET2
                else:
                    # TODO: redistribute cards and reset game
                    self.init_bets()
                    self._phase = BeloteGame.GamePhase.DEAL
                    self.dealer = self.next_player_to_deal()
        else:
            print ("Player took")
            # Deal reamining cards
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

    def allowed_bets(self, player):
        allowed_bets = []
        # if self.hands.get(player) is None:
        #     allowed_bets = []  # No hand yet
        if self.get_game_phase() == self.GamePhase.BET:
            allowed_bets = ['Pass', str(self.trump_suit)]
        elif self.get_game_phase() == self.GamePhase.BET2:
            allowed_bets = ['Pass']
            for suit in Card.SUIT_NAMES:
                if suit != self.trump_suit:
                    allowed_bets.append(suit)

        print("allowed bets:", allowed_bets)
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
            # TODO: If player has trump, must play it
            if len(allowed_cards) == 0:
                allowed_cards = self.hands[player].serialize()
        return allowed_cards

    def update_scores(self):
        # Calculate the total points of cards in round

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

        # Pick up trump card
        self.trump_card = self.deck.deal()
        self.trump_suit = self.trump_card.get_suit_name()

        self._phase = BeloteGame.GamePhase.BET
        return self.hands

    # Distribute 3 cards for each player
    def deal_2(self, dealer=""):
        print("In deal_2")
        print ("Trum card:", self.trump_card)

        # Taker takes the trump card then two more
        self.hands[self.taker].add(self.trump_card)
        for i in range(2):
            self.hands[self.taker].add(self.deck.deal())
        self.hands[self.taker].sort()

        # Other players take 3 cards
        for player in self.get_playing_players():
            if player != self.taker:
                for i in range(3):
                    self.hands[player].add(self.deck.deal())
                self.hands[player].sort()
        return self.hands

    # TODO: change this to be based on score reaching a certain threshold
    def is_game_over(self):
        return self._current_hand_nb == len(self._nb_cards_per_hand)

    def round_ended(self, winner):
        cards_per_player = self.current_round.cards_played
        points = 0
        for player in cards_per_player:
            print("Player: " + player)
            print (cards_per_player)
            card = str(cards_per_player[player])
            print("Card: " + card)
            points = points + self.card_points[card]
        print("Points in round:" + str(points))
        self.hand_points[winner] += points
        return points

    def set_cards_rank_and_value(self):
        suit_char = self.trump_card.get_suit()
        self.card_points[suit_char+"9"] = 14
        self.card_points[suit_char+"11"] = 20
        self.card_ranks[suit_char + "9"] = 16
        self.card_ranks[suit_char + "11"] = 17
        for card in self.deck.cards:
            card.rank = self.card_ranks[str(card)]
            card.points = self.card_points[str(card)]

    def init_dict(self, a_dict, value):
        for player in self.players:
            a_dict[player] = value

    def init_bets(self):
        self.init_dict(self.bets, "")