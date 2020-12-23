from enum import Enum
from random import choice
from random import randrange
from ..card import Card
from ..deck import Deck
from ..hand import Hand
from ..round import Round

class BeloteGame():

    class GamePhase(Enum):
        DEAL = "Deal"
        BET = "Bet"
        BET2 = "Bet2"
        PLAY = "Play"

    def __init__(self, game_creator = "", bonus_win = 1, deck_size=32):
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
        self.owner = game_creator
        self.active_player = self.owner
        self.deck_size = deck_size
        self._nb_cards_per_hand=None
        self._current_hand_nb = 0
        self._started = False;
        self._phase = BeloteGame.GamePhase.DEAL
        self.scoresheet=[]
        self._player_status=dict()
        self.init_dict(self._player_status, 1)
        self.taker = None

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
        self.taker = None

    def get_game_phase(self):
        return self._phase

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
            self.game_phase = BeloteGame.GamePhase.DEAL
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
            self.game_phase = BeloteGame.GamePhase.DEAL
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

        # Set deck size based on number of players
        self.deck_size = 32

        # Create hand progression
        self._phase = BeloteGame.GamePhase.BET

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

        if (bet == 0):
            # Ask next player
            self.active_player = self.next_player(player)
            if self.next_player_to_bet(player) is None:
                # TODO: if first round of betting then move to second round. Phase shoulb be BET2
                if self._phase == BeloteGame.GamePhase.BET:
                    self._phase = BeloteGame.GamePhase.BET2
                else:
                    self._phase = BeloteGame.GamePhase.PLAY
        else:
            # Start the play phase
            self._phase = BeloteGame.GamePhase.PLAY
            # TODO: active player must now be the one after the one that dealt the cards

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
            # TODO: If player has trump, must play it
            if len(allowed_cards) == 0:
                allowed_cards = self.hands[player].serialize()
        return allowed_cards

    def get_current_round(self):
        return self.current_round

    def update_scores(self):
        # TODO: may have to change to playing players only?
        # TODO: count score based on cards in winned rounds
        for p in range(len(self.players)):
            player = self.players[p]

         #self.scoresheet.append([self.bets.copy(), self.wins.copy(), self.scores.copy()])

        return self.scores

    def get_scores(self):
        return self.scores

    def all_rounds_played(self):
        return self.current_round.last_card_played()

    # Iniial deal of 5 card per player
    def deal1(self, dealer=""):
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()
        self.init_dict(self.bets,-1)
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
        trump_card = self.deck.deal()
        self.trump_card = trump_card

        self._phase = BeloteGame.GamePhase.BET
        return self.hands

    # Distribute 3 cards for each player
    def deal2(self, dealer=""):
        # TODO: player that won the bet takes the trump card
        for i in range(3):
            for player in self.get_playing_players():
                if player != self.taker:
                    self.hands[player].append(self.deck.deal())


    # TODO
    def get_nb_cards_to_deal(self):
        return 0

    # TODO
    def get_play_with_trump(self):
        return True

    def is_game_over(self):
        return self._current_hand_nb == len(self._nb_cards_per_hand)

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
