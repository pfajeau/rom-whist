import logging

class GameState:

    def __init__(self, game_id):
        self.game_id = game_id
        self.trump = ""
        self.cards_played = []
        self.card_played_round = []
        self.partner = ""
        self.card_played_by_suit = dict()
        self.card_played_by_player = dict()
        self.deck_size = 0
        self.hand_cards = []
        self.hand_cards_as_str = ""


