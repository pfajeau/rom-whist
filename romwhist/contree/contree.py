import copy
from flask_babel import lazy_gettext as _l
from flask_babel import gettext as _
import logging
from enum import Enum

from romwhist.card import Card
from romwhist.belote.belote import BeloteGame
from romwhist.contree.contree_state import ContreeState
from romwhist.contree.announce import Announce
from romwhist.contree.announce import ContreStatus


class CountingMethod(str, Enum):
    POINTS_ACHIEVED = "points_achieved"
    POINTS_BID = "points_bid"
    POINTS_ACHIEVED_PLUS_BID = "points_achieved_bid"


class ContreeGame(BeloteGame):

    all_bet_points = [80, 90, 100, 110, 120, 130, 140, 150, 162]

    def __init__(self, game_creator="", id=0, counting=CountingMethod.POINTS_BID):
        BeloteGame.__init__(self, game_creator, id)
        # Number of cards to deal depending on number of players
        self.nb_cards_first_deal = {1: 8, 2: 8, 3: 8, 4: 8}
        self.current_bet = Announce.from_str("pass_0")
        self.contree_status = ContreStatus.NORMAL
        self.counting = counting
        self.init_bets()
        self.active_player = game_creator

        self.BONUS_CAPOT = 250

        # THose are there so that these strings are extracted in pot file for i18n
        self.__PASS = _("pass")
        self.__CONTRE = _("contre")
        self.__SURCONTRE = _("surcontre")
        self.__POINTS_BID = _("points_bid")
        self.__POINTS_ACHIEVED = _("points_achieved")
        self.__POINTS_ACHIEVED_BID = _("points_achieved_bid")


    def get_state(self):
        state = ContreeState(self.id)
        self.populate_state(state)
        state.contree_status = self.contree_status
        for player in self.players:
            state.bets[player] = str(self.bets[player])
        state.current_bet = str(self.current_bet)

        return state

    def set_state(self, state):
        BeloteGame.set_state(self,state)
        self.contree_status = state.contree_status
        for player in self.players:
            self.bets[player] = Announce.from_str(state.bets[player])
        self.current_bet = Announce.from_str(state.current_bet)

    def place_bet(self, player, bet, ai=False):
        logging.info("Player " + player + " bet: " + str(bet))
        self.bets[player] = bet
        move_to_play_phase = False

        logging.info("Player bet: %s", bet.suit)

        if bet.suit == "contre":
            self.contree_status = ContreStatus.CONTREE
            next_player_to_bet = self.next_player(player)
            logging.info("Next player to bet %s ", next_player_to_bet)
            self.active_player = next_player_to_bet
            self._nb_pass_since_bet = 0

        elif bet.suit == "surcontre":
            move_to_play_phase = True
            self.contree_status = ContreStatus.SURCONTREE
            # if player == self.taker:
            #     self.bets[player] = self.current_bet

        elif bet.suit == "pass":
            logging.info("Player passed")
            self._nb_pass_since_bet += 1

            # Ask next player
            next_player = self.next_player(player)
            next_player_to_bet = self.next_player_to_bet(player, "_0")
            logging.info("Next player to bet %s ", next_player_to_bet)
            self.active_player = self.next_player(player)

            if next_player_to_bet is None:
                # if self.contree_status == ContreStatus.CONTREE and self.taker == player:
                #     self.bets[player] = self.current_bet

                if self.bets[next_player].suit == "pass":
                    self.init_bets()
                    self.phase = BeloteGame.GamePhase.DEAL
                    self.dealer = self.next_player_to_deal()
                else:
                    move_to_play_phase = True

        elif bet.points == self.TOTAL_POINTS:
            self._nb_pass_since_bet = 0
            self.current_bet = bet
            self.taker = player
            self.active_player = self.next_player(player)

        elif self.next_player_to_bet(player) is None:
            # Move to PLAY phase
            move_to_play_phase = True

        else:
            self.active_player = self.next_player(player)

            if self.current_bet is None or \
                    bet.points > self.current_bet.points or \
                    ai or \
                    self.current_bet.suit == "pass":
                self._nb_pass_since_bet = 0
                self.current_bet = bet
                self.trump_suit = bet.suit    # Required for AI
                self.taker = player
            else:
                logging.error("Invalid Bet: %s", bet)
                logging.error("self.current_bet: %s", self.current_bet)

        if self.current_bet is not None:
            self.trump_suit = self.current_bet.suit

        if move_to_play_phase:
            self.phase = BeloteGame.GamePhase.PLAY
            self.set_cards_rank_and_value()
            self.active_player = self.next_player(self.dealer)
        return


    def get_allowed_bets(self, player):
        allowed_bets_points = []
        allowed_bets_suits = []
        if self.current_bet is None:
            current_bet_points = 0
        else:
            current_bet_points = self.current_bet.points
            
        if self.contree_status != ContreStatus.CONTREE and \
                self.contree_status != ContreStatus.SURCONTREE and \
                current_bet_points != 162:
            allowed_bets_suits = copy.deepcopy(Card.SUIT_NAMES)
            if self.phase == self.GamePhase.BET:
                if self.current_bet is None:
                    allowed_bets_points = copy.deepcopy(ContreeGame.all_bet_points)
                else:
                    for bet in ContreeGame.all_bet_points:
                        if bet > self.current_bet.points:
                            allowed_bets_points.append(bet)

        allowed_bets_suits.insert(0, "pass")

        # Add Contree or Surcontree option
        if self.contre_enabled(player):
            allowed_bets_suits.append("contre")
            #allowed_bets_points.append(0)
        elif self.surcontre_enabled(player):
            allowed_bets_suits.append("surcontre")
            #allowed_bets_points.append(0)

        allowed_bets = [allowed_bets_suits, allowed_bets_points]
        logging.debug("allowed bets:%s %s", allowed_bets[0], allowed_bets[1])
        return allowed_bets

    def contre_enabled(self, player):
        # True if one player has bet before and player is not partner
        partner = self.next_player(self.next_player(player))

        if self.contree_status == ContreStatus.CONTREE or \
           self.contree_status == ContreStatus.SURCONTREE or \
           self.taker == partner or \
           self.current_bet is None or \
           self.current_bet.suit == "pass":
            logging.debug("Contre disabled")
            return False

        else:
            logging.debug("Contre enabled")
            return True

    def surcontre_enabled(self, player):
        # True if one player has contre and is not partner
        partner = self.next_player(self.next_player(player))
        if self.contree_status == ContreStatus.CONTREE and \
           (self.taker == partner or self.taker == player):
            return True
        else:
            return False

    def deal(self, dealer=""):
        self.current_bet = None
        self.contree_status = ContreStatus.NORMAL
        return self.deal_cards(int(self.deck_size / len(self.players)), dealer)

    def deal_2(self, dealer=""):
        return

    def add_player(self, player):
        if len(self.get_playing_players()) >= 4:
            return None

        BeloteGame.add_player(self, player)
        if player in self.players:
            self.init_bets()
        else:
            self.bets[player] = Announce("", "")
        return player

    def init_bets(self):
        for player in self.players:
            self.bets[player] = Announce("", 0)


    def update_scores(self):
        # Check each player points
        # If 2 or 3 players, player that took need to have more points that other players to win
        # if 4 players, player that took and partner need to have more points than other players
        nb_players = len(self.players)
        players = []
        players.append(self.taker)
        player_points = []
        player_points.append(self.hand_points[self.taker])
        self.__hand_winner = []

        for i in range(1, nb_players):
            players.append(self.next_player(players[i - 1]))
            player_points.append(self.hand_points[players[i]])

        for i in range(nb_players):
            if self.belote_state == BeloteGame.BeloteState.Rebelote_Played and \
                    self.player_with_belote == players[i]:
                logging.info("In update_scores, adding belote / rebelote points to " + players[i])
                player_points[i] += self.BELOTE_REBELOTE
                self.hand_points[players[i]] = player_points[i]

        # TODO: remove test (always 4 players) and add support for contree / surcontree
        if nb_players == 4:
            logging.debug("Bet points: %s", self.bets[players[0]].points)
            if self.player_with_belote is not None:
                # set score of partner of player who may have gotten
                # the belote points to be the same
                partner = self.next_player(self.next_player(self.player_with_belote))
                self.scores[partner] = self.scores[self.player_with_belote]

            score_winners = 0
            score_losers = 0
            if player_points[0] + player_points[2] >= self.bets[players[0]].points:
                if self.counting == CountingMethod.POINTS_ACHIEVED:
                    score_winners = round(player_points[0] + player_points[2])
                    score_losers = round(player_points[1] + player_points[3])
                elif self.counting == CountingMethod.POINTS_BID:
                    score_winners = round(player_points[0] + player_points[2])
                    score_losers = 0
                elif self.counting == CountingMethod.POINTS_ACHIEVED_PLUS_BID:
                    score_winners = round(player_points[0] + player_points[2] + self.current_bet.points, -1)
                    score_losers = player_points[1] + player_points[3]

                self._hand_winner.append(players[0])
                self._hand_winner.append(players[2])

                # Contree
                if self.contree_status == ContreStatus.CONTREE:
                    score_winners = 2 * score_winners
                elif self.contree_status == ContreStatus.SURCONTREE:
                    score_winners = 4 * score_winners

                self.scores[players[0]] += score_winners
                self.scores[players[2]] = self.scores[players[0]]
                self.scores[players[1]] += score_losers
                self.scores[players[3]] += self.scores[players[1]]

            else:
                score_winners = round(self.TOTAL_POINTS, -1)
                if self.contree_status == ContreStatus.CONTREE:
                    score_winners = 2 * score_winners
                elif self.contree_status == ContreStatus.SURCONTREE:
                    score_winners = 4 * score_winners

                self.scores[players[1]] = score_winners
                self.scores[players[3]] = self.scores[players[1]]
                self._hand_winner.append(players[1])
                self._hand_winner.append(players[3])

            # Capot
            if self.counting == CountingMethod.POINTS_ACHIEVED or \
               self.counting == CountingMethod.POINTS_ACHIEVED_PLUS_BID or \
               self.counting == CountingMethod.POINTS_BID and self.current_bet.points == self.TOTAL_POINTS:

                if self.contree_status == ContreStatus.CONTREE:
                    points_capot = self.BONUS_CAPOT * 2
                elif self.contree_status == ContreStatus.SURCONTREE:
                    points_capot = self.BONUS_CAPOT * 4
                else:
                    points_capot = self.BONUS_CAPOT

                if self.wins[players[1]] + self.wins[players[3]] == 0:
                    self.scores[players[0]] += points_capot
                    self.scores[players[2]] = self.scores[players[0]]
                elif self.wins[players[0]] + self.wins[players[2]] == 0:
                    self.scores[players[1]] += points_capot
                    self.scores[players[3]] = self.scores[players[1]]

        logging.debug("Bet %s", self.current_bet)
        logging.debug("Player points: %s", player_points)
        logging.debug("Hand Winners: %s", self._hand_winner)
        self.scoresheet.append(self.scores.copy())
        return self.scores
