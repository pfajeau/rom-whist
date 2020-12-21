from ..game import CardGame

class OhellGame(CardGame):

    def __init__(self, game_creator = "", bonus_win = 1, deck_size=0):
        CardGame.__init__(self, game_creator, bonus_win, deck_size)
