from enum import Enum
from random import choice
from random import randrange
from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.hand import Hand
from romwhist.round import Round

class CardGame():

    MANUAL_DEALING = "manual"
    AUTOMATED_DEALING = "automated"

    class GamePhase(Enum):
        DEAL = "Deal"
        BET = "Bet"
        PLAY = "Play"

    def __init__(self, game_creator = "", deck_size=0):
        self.players = []
        self.current_round = None
        self.trump_card = None
        self.hands=dict()
        self.scores=dict()
        self.bets=dict()
        self.wins=dict()
        self.points=dict()
        self.dealer = None
        self.init_dict(self.scores,0)
        self.dealing_method = CardGame.AUTOMATED_DEALING
        self.owner = game_creator
        self.active_player = self.owner
        self.deck_size = deck_size
        self._current_hand_nb = 0
        self._started = False;
        self._phase = CardGame.GamePhase.DEAL
        self.scoresheet=[]
        self._player_status=dict()
        self.init_dict(self._player_status, 1)
        self.trump_suit=None
        self.rounds = []   # The rounds for the hand

    def reset(self):
        self.current_round = None
        self.trump_card = None
        self.hands=dict()
        self.scores=dict()
        self.bets=dict()
        self.wins=dict()
        self.points = dict()
        self.dealer = None
        self.init_dict(self.scores,0)
        self.active_player = self.owner
        self.init_bets()
        self.init_dict(self.wins, 0)
        self._current_hand_nb = 0

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
            self.game_phase = CardGame.GamePhase.DEAL
            self.current_round = None
            # self.trump_card = None
            self.bets = dict()
            self.wins = dict()
            self.init_bets()
            self.init_dict(self.wins, 0)

        else:
            self.players.append(player)
            self._player_status[player] = 1
            self.scores[player] = 0
            self.bets[player] = -1
            self.wins[player] = 0
            self.points[player] = 0

    def disable_player(self, player):
        print("In Game.disable_player, disabloing playerL " + player)
        if player in self.players:
            self._player_status[player] = 0
            print(self._player_status)
            if player == self.dealer:
                self.dealer = self.next_player_to_deal()
            self.active_player = self.dealer
            self.game_phase = CardGame.GamePhase.DEAL
            self.current_round = None
            self.bets = dict()
            self.wins = dict()
            self.init_bets()
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
        if self.dealing_method == CardGame.AUTOMATED_DEALING:
            self._phase = CardGame.GamePhase.BET
            self.create_hand_progression()
        else:
            self._phase = CardGame.GamePhase.DEAL

    def get_hand(self, player):
        return self.hands[player]

    def get_hands(self):
        return self.hands

    def get_bets(self):
        return self.bets

    def get_wins(self):
        return self.wins;

    def round_ended(self, winner):
        return

    # Return a dictionary of cards played per player for the current round
    def get_cards_played(self):
        if len(self.rounds) > 0:
            cards = self.rounds[-1].cards_played
            card_played_as_str = dict()
            for player in cards:
                card_played_as_str[player] = str(cards[player])
            return card_played_as_str
        else:
            return None

    def hand_completed(self):
        self.update_scores()

    def is_hand_completed(self):
        for player in self.get_playing_players():
            if len(self.hands[player].get_cards()) > 0:
                return False
        return True

    def create_round(self):
        if self.trump_card is None:
            suit = None
        else:
            suit = self.trump_suit
        self.current_round = Round(self.get_playing_players(), suit)
        self.rounds.append(self.current_round)
        return self.current_round

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
    def card_played(self, player, card_value):
        print(player + " played: " + card_value)
        # Find card in hand that matches card played and remove it from hand
        for card in self.hands[player].get_cards():
            if str(card) == card_value:
                # Remove card from player hands
                self.hands[player].remove(card)
                self.current_round.card_played(player, card)
        if self.current_round.last_card_played():
            winner = self.current_round.compute_winner()
            self.wins[winner] = self.wins[winner] + 1
            if self.is_hand_completed():
                self.active_player = self.next_player_to_deal()
            else:
                self.active_player = winner

            self.round_ended(winner)
            return winner
        else:
            self.active_player = self.next_player(player)
            return None

    # By default allows any card.
    def get_allowed_cards(self, player):
        allowed_cards = self.hands[player].serialize()
        return allowed_cards

    def get_current_round(self):
        return self.current_round

    # Default behavoir does nothing
    def update_scores(self):
        return self.scores

    def get_scores(self):
        return self.scores

    def all_rounds_played(self):
        return self.current_round.last_card_played()

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


    def init_bets(self):
        self.init_dict(self.bets, -1)