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
        self._cards_as_str = ""
        self.vd = 0

        self.__state = GameState(game_id)
        print("Hello World!")

    @property
    def state(self):
        return self.__state

    @property
    def cards_as_str(self):
        return self.state.hand_cards_as_str

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
    def game_id(self):
        return self.__state.game_id

    @game_id.setter
    def game_id(self, value):
        self.state.game_id = value

    def game_started(self, deck_size):
        self.state.deck_size = deck_size
        #self.__deck_size=deck_size

    def player_to_bet(self, allowed_bets):
        return allowed_bets[0]

    def player_to_play(self, allowed_cards):
        # TOOD
        logging.debug("AI PLayer to play: %s", self.name)
        logging.debug("Allowed cards: %s", allowed_cards)
        return allowed_cards[0]

    def new_hand(self, cards):
        self.state.hand_cards = []
        for card in cards:
            self.state.hand_cards.append(Card.card_from_value(card))
        logging.debug("In new hand, cards: %s", len(self.state.hand_cards))
        self.state.hand_cards_as_str = cards

    def compute_deck_value(self):
        # Calculate average value of hand
        deck = Deck(self.state.deck_size)
        cards = deck.all_cards
        self.vd = 0
        for card in cards:
            self.vd += self.compute_card_value(str(card))
        logging.info("Deck value: %s", self.vd)

    def compute_card_value(self, card):
        # Returns card value between 0 and 100
        my_card = Card.card_from_value(card)
        r = 14 - my_card.rank
        nr = self.state.deck_size / 4
        cv = ((nr - r) * 50) / 8

        # Trump card: add 50 points
        if my_card.get_suit() == self.__state.trump:
            cv += 50
        logging.debug("Card value for %s is: %s", card, cv)
        return cv


