import copy
import logging
from romwhist.belote.belote import BeloteGame
from romwhist.belote.belote_state import BeloteState


class ContreeGame(BeloteGame):
    all_bet_points = [80, 90, 100, 110, 120, 130, 140, 150, "Capot"]

    class Announce:
        def __init__(self, suit, points):
            self.suit = suit
            self.points = points

        def __str__(self):
            return self.suit + "_" + str(self.points)

        def __gt__(self, other):
            if other.points == "Capot" and self.points != "Capot":
                return False
            return self.points > other.points

        @classmethod
        def from_str(cls, announce_as_string):
            suit, points = announce_as_string.split("_", 1)
            return cls(suit, points)

    def __init__(self, game_creator="", id=0):
        BeloteGame.__init__(self, game_creator, id)
        BeloteGame.nb_cards_first_deal = {1: 8, 2: 8, 3: 8, 4: 8}
        self.current_bet = None

    def place_bet(self, player, bet):
        logging.info("Player " + player + "bid: " + str(bet))
        self.bets[player] = bet

        if bet.suit == "Pass":
            logging.info("Player passed")
            # Ask next player
            next_player = self.next_player(player)
            next_player_to_bet = self.next_player_to_bet(player)
            if next_player_to_bet is None:
                if self.bets[next_player] == "Pass":
                    self.init_bets()
                    self.phase = BeloteGame.GamePhase.DEAL
                    self.dealer = self.next_player_to_deal()
                else:
                    self.phase = BeloteGame.GamePhase.PLAY
                    self.active_player = self.next_player(self.dealer)
            return

        if bet.points == "Capot" or self.next_player_to_bet(player) is None:
            # Move to PLAY phase
            self.phase = BeloteGame.GamePhase.PLAY
            self.trump_suit = bet.suit
            self.taker = player
            self.set_cards_rank_and_value()
            self.active_player = self.next_player(self.dealer)
        else:
            self.active_player = self.next_player(player)

            if self.current_bet is None:
                self.current_bet = bet
            elif bet > self.current_bet:
                self.current_bet = bet
            else:
                logging.error("Invalid Bet: %s", bet)

        return

    # Return None if all players have bet
    def next_player_to_bet(self, player):
        logging.debug("Next player to bet after: " + player)
        next_player = self.next_player(player)
        # If three other players than nplayers have passed and next_player has a bet
        # then move on to the play phase
        # If next player has passed and three other players have passed, then return None
        # If next_player has not bet then they are the next player to bet
        if self.bets[next_player] is None:
            return next_player

        players = []
        players[0] = player
        for i in range(1, len(self.players) - 1):
            players[i] = self.next_player(players[i - 1])
            if players[i] != next_player and self.bets[players[i]] != "Pass":
                return next_player

        # All 3 other players have passed
        # Could mean hand needs to be re-done (if next_player has passed,
        # or that game can start (if next_player has announced something)
        # But case where next_player is the first to announce something? Other players
        # that may have passed before have a change to announce as well. So need to be
        # smarter TODO
        return None

    def get_allowed_bets(self, player):
        allowed_bets = []
        if self.phase == self.GamePhase.BET:
            if self.current_bet is None:
                allowed_bets = copy.deepcopy(ContreeGame.all_bet_points)
            else:
                for bet in ContreeGame.all_bet_points:
                    if bet != "Capot":
                        if bet > self.current_bet.points:
                            allowed_bets.append(bet)
                allowed_bets.append("Capot")

        logging.debug("allowed bets:" + str(allowed_bets))
        return allowed_bets

    def deal(self, dealer=""):
        return self.deal_cards(int(self.deck_size / len(self.players)), dealer)

    def init_bets(self):
        for player in self.players:
            self.bets[player] = None
