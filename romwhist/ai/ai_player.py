import logging

from romwhist.game_state import GameState
from romwhist.card import Card
from romwhist.deck import Deck


class AiPlayer:

    def __init__(self, name, game_id):
        self.__name = name
        self.__cards = []
        self.suit=""
        self.__deck_size = 0
        self._cards_as_str = []
        self.vd = 0
        self.__game_state = None
        self.trump_card = ""
        self.game_id = game_id
        self.game_state = None

        print("Hello World!")

    @property
    def game_state(self):
        return self.__game_state

    @game_state.setter
    def game_state(self, value):
        self.__game_state = value

    @property
    def cards_as_str(self):
        return self._cards_as_str

    @property
    def cards(self):
        return self.__cards

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value


    @property
    def deck_size(self):
        return self.__deck_size


    def game_started(self, deck_size, players):
        logging.debug("Game started. Deck size: %s", deck_size)
        # self.__deck_size = deck_size
        # self.game_state.players = players
        # #self.__deck_size=deck_size

    def set_trump(self, trump_card, trump_suit):
        self.trump_card = trump_card
        self.game_state.trump = trump_suit

    def player_to_bet(self, allowed_bets):
        return allowed_bets[0]

    def player_bet(self, player, bet):
        #self.game_state.bets[player] = bet
        return

    def player_to_play(self, allowed_cards):
        # TOOD
        logging.debug("AI PLayer to play: %s", self.name)
        logging.debug("Allowed cards: %s", allowed_cards)
        # Retrieve state from data (as JASON)
        # self.game_state = OhellState()
        return allowed_cards[0]

    def card_played(self, player, card):
        # self.game_state.cards_played_per_player[player].append(card)
        # self.game_state.cards_played.append(card)
        # #self.game_state.cards_played_per_round.append(card)
        # self.game_state.deck.remove_card(card)
        # suit = Card.card_from_value(card).get_suit()
        # self.game_state.cards_played_by_suit[suit].append(card)
        return

    def new_hand(self, cards):
        # for card in cards:
        #     self.my_hand.append(Card.card_from_value(card))
        #     self._cards_as_str.append(card)
        # # self.game_state.hand_cards = []
        # self.game_state.cards_played_per_player = dict()
        #
        # for player in self.game_state.players:
        #     self.game_state.cards_played_per_player[player] = []
        #
        # self.game_state.deck = Deck(self.game_state.deck_size)
        # for card in cards:
        #     self.game_state.hand_cards.append(Card.card_from_value(card))
        # logging.debug("In new hand, cards: %s", len(self.my_hand))
        return

    def compute_deck_value(self):
        # Calculate average value of hand
        deck = Deck(self.__deck_size)
        cards = deck.all_cards
        self.vd = 0
        for card in cards:
            self.vd += self.compute_card_value(str(card))
        logging.info("Deck value: %s", self.vd)

    def compute_card_value(self, card):
        # Returns card value between 0 and 100
        my_card = Card.card_from_value(card)
        r = 14 - my_card.rank
        nr = self.__deck_size / 4
        cv = ((nr - r) * 50) / 8

        logging.debug ("r: %s, nr: %s, deck_size: %s, cv: %s", r, nr, self.deck_size, cv)
        # Trump card: add 50 points
        if my_card.get_suit() == self.__game_state.trump:
            cv += 50
        logging.debug("Card value for %s is: %s", card, cv)
        return cv


