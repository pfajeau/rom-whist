import copy
import json

from romwhist.player import Player


class GameState:

    def __init__(self, game_id, sim_player=None, players=[], trump="", cards_played_per_player=None,
                 cards_played_per_round=dict(), deck_size=0,
                 hand_cards=dict(), allowed_cards=[], active_player=None, scores=dict(),
                 owner=None, dealer=None, bets=dict(), allowed_bets=[], trump_card="", hand_points=dict(),
                 players_status=dict(), players_type=dict()):
        self.game_id = game_id
        self.players = players
        self.trump = trump
        self.cards_played_per_player = cards_played_per_player
        self.deck_size = deck_size
        self.hand_cards = hand_cards
        self.allowed_cards = allowed_cards
        self.active_player = active_player
        self.cards_played_per_round = cards_played_per_round
        self.scores = scores
        self.owner = owner
        self.dealer = dealer
        self.allowed_bets = allowed_bets
        self.sim_player = sim_player
        self.bets = bets
        self.trump_card = trump_card
        self.hand_points = hand_points

        self.players_status = players_status
        self.players_type = players_type
        self.make_serializable()

    def make_serializable(self):
        # Convert Player objects to strings if necessary
        for player in self.players:
            if isinstance(player, Player):
                self.players_status[player.name] = player.player_status
                self.players_type[player.name] = player.player_type
                self.players[self.players.index(player)] = player.name

        if isinstance(self.active_player, Player):
            self.active_player = self.active_player.name
        if isinstance(self.dealer, Player):
            self.dealer = self.dealer.name
        if isinstance(self.owner, Player):
            self.owner = self.owner.name

        # Convert dictionaries use string as keys
        self.convert_dict_to_string(self.bets)
        self.convert_dict_to_string(self.hand_points)
        self.convert_dict_to_string(self.scores)
        self.convert_dict_to_string(self.bets)
        self.convert_dict_to_string(self.cards_played_per_player)

    # Can be calculated
        # self.cards_played = []
        # self.cards_played_by_suit = {'c':[], 'd':[], 'h':[], 's':[]}
        # self.hand_cards_as_str = ""

    @staticmethod
    def convert_dict_to_players(a_dict, players_dict):
        for key in a_dict.keys():
            if isinstance(key, str):
                value = a_dict[key]
                del a_dict[key]
                new_key = players_dict[key]
                a_dict[new_key] = value
        return a_dict

    @staticmethod
    def convert_dict_to_string(a_dict):
        for key in a_dict.keys():
            if isinstance(key, Player):
                value = a_dict[key]
                del a_dict[key]
                new_key = key.name
                a_dict[new_key] = value

    def get_legal_actions(self):
        return self.allowed_cards

    def get_legal_bets(self):
        allowed_bets = []
        for bet in self.allowed_bets:
            allowed_bets.append(str(bet))

        return allowed_bets

    def to_json(self):
        # for player in self.players:
        #     self_copy.players_status[player.name] = player.player_status
        #     self_copy.players_type[player.name] = player.player_type
        #     player_name = player.name
        #     self_copy.players[self.players.index(player)] = player.name
        #
        # self_copy.active_player = self.active_player.name
        # self_copy.dealer = self.dealer.name
        # self_copy.owner = self.owner.name

        # Convert dictionaries that use a string player as key to
        # using a player object as key
        # self.convert_dict_to_players(self.players_status, players_dict)
        # self.convert_dict_to_players(self.players_type, players_dict)
        # self.convert_dict_to_string(self_copy.bets)
        # self.convert_dict_to_string(self_copy.hand_points)
        # self.convert_dict_to_string(self_copy.scores)
        # self.convert_dict_to_string(self_copy.bets)
        # self.convert_dict_to_string(self_copy.cards_played_per_player)

        return json.dumps(self.__dict__)

    def next_player(self, player):
        pos = self.players.index(player)
        if pos == len(self.players) - 1:
            return self.players[0]
        else:
            return self.players[pos + 1]
