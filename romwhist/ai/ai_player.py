from romwhist.card import Card


class AiPlayer:

    def __init__(self, name, game_id):
        self.__name = name
        self.__game_id = game_id
        self.__cards = []
        print("Hello World!")

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def game_id(self):
        return self.__game_id

    @game_id.setter
    def game_id(self, value):
        self.__game_id = value

    def player_to_bet(self, allowed_bets):
        # TOOD
        return allowed_bets[0]

    def player_to_play(self, allowed_cards):
        # TOOD
        return allowed_cards[0]

    def new_hand(self, cards):
        for card in cards:
            self.__cards = []
            self.__cards.append(Card.card_from_value(card))
