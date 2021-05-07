import copy
import logging
from enum import Enum

from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.game_state import GameState
from romwhist.hand import Hand
from romwhist.round import Round


class CardGame:
    MANUAL_DEALING = "manual"
    AUTOMATED_DEALING = "automated"

    class GamePhase(str, Enum):
        DEAL = "Deal"
        BET = "Bet"
        PLAY = "Play"
        OVER = "Over"
    def __init__(self, game_creator="", deck_size=0, id=0):
        self.players = []
        self.current_round = None
        self.trump_card = None
        self.hands = dict()
        self.scores = dict()
        self.bets = dict()
        self.wins = dict()
        self.points = dict()
        self.dealer = None
        self.init_dict(self.scores, 0)
        self.dealing_method = CardGame.AUTOMATED_DEALING
        self.__owner = game_creator
        self.active_player = self.owner
        self.deck_size = deck_size
        self._current_hand_nb = 0
        self._started = False
        self.phase = CardGame.GamePhase.DEAL
        self.scoresheet = []
        self._player_status = dict()
        self.init_dict(self._player_status, 1)
        self.trump_suit = None  # E.g. "spade", or "heart"
        self.rounds = []  # The rounds for the hand
        self.__id = id
        self.deck = None
        self.hand_points = dict()
        self.init_dict(self.points, 0)

    def reset(self):
        self.current_round = None
        self.trump_card = None
        self.hands = dict()
        self.scores = dict()
        self.bets = dict()
        self.wins = dict()
        self.points = dict()
        self.dealer = None
        self.init_dict(self.scores, 0)
        self.active_player = self.owner
        self.init_bets()
        self.init_dict(self.wins, 0)
        self._current_hand_nb = 0

    def populate_state(self, state:GameState):
        # Populate state
        state.game_id = self.__id
        state.players = self.get_playing_players()
        state.trump = self.trump_suit
        state.cards_played_per_player = self.get_cards_played_per_player()
        state.deck_size = self.deck_size
        state.scores = self.scores
        state.owner = self.owner
        for player in self.get_playing_players():
            state.hand_cards[player] = self.hands[player].serialize()
        state.active_player = self.active_player
        state.dealer = self.dealer
        state.hand_points = copy.deepcopy(self.hand_points)

        i = 0
        state.cards_played_per_round = dict()
        for round in self.rounds:
            state.cards_played_per_round[i] = dict()
            for player in self.get_playing_players():
                state.cards_played_per_round[i][player] = str(round.cards_played.get(player))
            i += 1

        state.hand_cards = dict()
        for player in self.hands:
            state.hand_cards[player] = self.hands[player].serialize()

        # if self.current_round is None:
        #     state.current_round = self.create_round()

        state.allowed_cards = self.get_allowed_cards(state.active_player)
        logging.debug("state.allowed_cards: %s", state.allowed_cards)

        state.bets = copy.deepcopy(self.bets)
        state.trump_card = str(self.trump_card)
        return copy.deepcopy(state)

    def set_state(self, state: GameState):
        self.reset()

        state_copy = copy.deepcopy(state)
        self.game_id = state_copy.game_id
        self.players = state_copy.players
        for player in state_copy.players:
            self._player_status[player] = 1
        self.trump_suit = state_copy.trump
        self.deck_size = state_copy.deck_size
        self.deck = Deck(state_copy.deck_size)
        self.scores = state_copy.scores
        self.soft_init_dict(self.scores, 0)
        self.owner = state_copy.owner
        self.dealer = state_copy.dealer
        self.hand_points = copy.deepcopy(state.hand_points)
        self.soft_init_dict(self.hand_points,0)
        self.active_player = state.active_player


        # Create hands
        for player in state_copy.hand_cards:
            self.hands[player] = Hand(self.deck)
            for card in state_copy.hand_cards[player]:
                self.hands[player].cards.append(Card.card_from_value(card))

        # Create rounds
        for round_nb in state_copy.cards_played_per_round:
            round = Round(state_copy.players, state_copy.trump)
            for player in state_copy.cards_played_per_round[round_nb]:
                card_str = state_copy.cards_played_per_round[round_nb].get(player)
                if card_str != 'None':
                    round.card_played(player,
                                      Card.card_from_value(card_str))
            self.rounds.append(round)
            self.current_round = round
        if self.current_round is None:
            self.current_round = self.create_round()

        self.active_player = state_copy.active_player
        self.bets = state_copy.bets
        if not state.trump_card is None and not state.trump_card == "":
            self.trump_card = Card.card_from_value(state.trump_card)

    @property
    def phase(self):
        return self.__phase

    @phase.setter
    def phase(self, value):
        self.__phase = value

    def get_active_player(self):
        return self.active_player

    @property
    def owner(self):
        return self.__owner

    @owner.setter
    def owner(self, player):
        self.__owner = player

    @property
    def started(self):
        return self._started

    # Set to true or false
    @started.setter
    def started(self, value):
        self._started = value

    @property
    def id(self):
        return self.__id

    # Return a list of players with the maximum score
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
            logging.info("player already exits - re-enabling")
            self._player_status[player] = 1
            # Need to re-start hands
            self.active_player = self.dealer
            self.phase = CardGame.GamePhase.DEAL
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
        if player in self.players:
            self._player_status[player] = 0
            if player == self.dealer:
                self.dealer = self.next_player_to_deal()
            self.active_player = self.dealer
            self.phase = CardGame.GamePhase.DEAL
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
        self.started = True
        self._current_hand_nb = 0

        # Set deck size based on number of players
        self.deck_size = len(self.players) * 8

        # Create hand progression
        if self.dealing_method == CardGame.AUTOMATED_DEALING:
            self.phase = CardGame.GamePhase.BET
            self.create_hand_progression()
        else:
            self.phase = CardGame.GamePhase.DEAL

    def get_hand(self, player):
        return self.hands[player]

    def get_hands(self):
        return self.hands

    def get_bets(self):
        return self.bets

    def get_wins(self):
        return self.wins

    def round_ended(self, winner):
        return

    # Return a dictionary of cards played per player for the current round
    def get_cards_played_current_round(self):
        if len(self.rounds) > 0:
            cards = self.rounds[-1].cards_played
            card_played_as_str = dict()
            for player in cards:
                card_played_as_str[player] = str(cards[player])
            return card_played_as_str
        else:
            return None

    def get_cards_played_per_player(self) -> dict:
        cards = dict()
        if len(self.rounds) > 0:
            for round in self.rounds:
                cards_round = round.cards_played
                for player in cards_round:
                    if cards.get(player) is None:
                        cards[player] = []
                    if not cards_round.get(player) is None:
                        cards[player].append(str(cards_round[player]))

            # for player in self.players:
            #     logging.debug("Cards played by %s: %s", player,  cards[player])
        return cards

    def hand_completed(self) -> None:
        self.update_scores()

    def is_game_over(self):
        return False

    def is_hand_completed(self):
        for player in self.get_playing_players():
            if len(self.hands[player].get_cards()) > 0:
                return False
        return True

    def create_round(self):
        self.current_round = Round(self.get_playing_players(), self.trump_suit)
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
    def play_card(self, player, card_value):
        logging.debug(player + " played: " + card_value)
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
            logging.debug("Winner of round is: " + winner)
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

    # Default behavior does nothing
    def update_scores(self):
        return self.scores

    def get_scores(self):
        return self.scores

    def all_rounds_played(self):
        return self.current_round.last_card_played()

    def next_player(self, player):
        pos = self.players.index(player)
        if pos == len(self.players) - 1:
            next_player = self.players[0]
        else:
            next_player = self.players[pos + 1]

        if self._player_status[next_player] == 1:
            return next_player
        else:
            return self.next_player(next_player)

    def init_dict(self, a_dict, value):
        for player in self.players:
            a_dict[player] = value

    def init_bets(self):
        self.init_dict(self.bets, -1)

    def soft_init_dict(self, a_dict, default_value):
        for player in self.players:
            if a_dict.get(player) is None:
                a_dict[player] = default_value

