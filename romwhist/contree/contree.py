"""
This module implements contree functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import copy
from flask_babel import gettext as _
import logging
from enum import Enum

from romwhist.card import Card
from romwhist.belote.belote import BeloteGame
from romwhist.belote.belote_status import BeloteStatus
from romwhist.contree.contree_state import ContreeState
from romwhist.contree.announce import Announce
from romwhist.contree.announce import ContreStatus
from romwhist.player import Player


class CountingMethod(str, Enum):
    POINTS_ACHIEVED = "points_achieved"
    POINTS_BID = "points_bid"
    POINTS_ACHIEVED_PLUS_BID = "points_achieved_bid"


class ContreeGame(BeloteGame):

    # 162 is the existing wire-format sentinel for a requested capot.
    all_bet_points = [80, 90, 100, 110, 120, 130, 140, 150, 160, 162]
    MAX_PLAYERS = 4
    MUST_UNDERTRUMP = False

    def __init__(self, game_creator=None, id=0, counting=CountingMethod.POINTS_BID):
        BeloteGame.__init__(self, game_creator, id)
        # Number of cards to deal depending on number of players
        self.nb_cards_first_deal = {1: 8, 2: 8, 3: 8, 4: 8}
        self.current_bet = Announce.from_str("pass_0")
        self.contree_status = ContreStatus.NORMAL
        self.counting = counting
        self.init_bets()
        self.active_player = Player(game_creator)

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
        new_state = self.populate_state(state)
        new_state.contree_status = self.contree_status
        for player in self.players:
            new_state.bets[player] = str(self.bets[player])
        new_state.current_bet = str(self.current_bet)
        new_state.counting = self.counting

        return new_state

    def populate_from_state(self, state):
        BeloteGame.populate_from_state(self, state)
        self.contree_status = ContreStatus(state.contree_status)
        self.counting = CountingMethod(state.counting)
        for player in self.players:
            self.bets[player] = Announce.from_str(state.bets[player])
        self.current_bet = Announce.from_str(state.current_bet)

    def place_bet(self, player, bet, ai=False):
        logging.info("Player " + player + " bet: " + str(bet))
        self.bets[player] = bet
        move_to_play_phase = False

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

        if move_to_play_phase or ai:
            self.phase = BeloteGame.GamePhase.PLAY
            # if not bet.suit == "pass":
            self.set_cards_rank_and_value()
            self.active_player = self.next_player(self.dealer)
            self.update_belote_status()

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
            # allowed_bets_points.append(0)
        elif self.surcontre_enabled(player):
            allowed_bets_suits.append("surcontre")
            # allowed_bets_points.append(0)

        allowed_bets = [allowed_bets_suits, allowed_bets_points]
        logging.debug("allowed bets:%s %s", allowed_bets[0], allowed_bets[1])
        return allowed_bets

    def contre_enabled(self, player):
        # True if one player has bet before and player is not partner
        partner = self.next_player(self.next_player(player))

        if self.contree_status == ContreStatus.CONTREE or \
           self.contree_status == ContreStatus.SURCONTREE or \
           self.taker in (partner, player) or \
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

    def deal(self, dealer=None):
        self.current_bet = None
        self.contree_status = ContreStatus.NORMAL
        hands = self.deal_cards(int(self.deck_size / len(self.players)), dealer)
        return hands

    def deal_2(self, dealer=None):
        return

    def add_player(self, player):
        if len(self.get_playing_players()) >= 4:
            return None

        BeloteGame.add_player(self, player)
        if player in self.players:
            self.init_bets()
        else:
            self.bets[player] = Announce("", "0")
        return player

    # def init_bet(self, player):
    #     self.bets[player] = ""
    #
    def init_bets(self):
        for player in self.players:
            self.bets[player] = Announce("", "0")

    @staticmethod
    def _round_score(points):
        # Python's round uses ties-to-even; the rules require 85 -> 90.
        return ((points + 5) // 10) * 10

    def update_scores(self):
        if self._hand_scored:
            return self.scores
        sides = self._scoring_sides()
        if len(sides) != 2 or len(self.players) != 4:
            raise ValueError("Contrée scoring requires two teams of two players")
        raw_points = [sum(self.hand_points[player] for player in side) for side in sides]
        bonuses = [self._belote_bonus(side) for side in sides]
        points = [raw + bonus for raw, bonus in zip(raw_points, bonuses)]
        tricks = [sum(self.wins[player] for player in side) for side in sides]
        capot = [count == 8 for count in tricks]
        bid = self.current_bet.points
        requested_capot = bid == self.TOTAL_POINTS
        success = capot[0] if requested_capot else points[0] >= bid
        multiplier = {ContreStatus.NORMAL: 1, ContreStatus.CONTREE: 2,
                      ContreStatus.SURCONTREE: 4}[self.contree_status]
        winner = 0 if success else 1
        awards = [0, 0]

        if self.counting == CountingMethod.POINTS_BID:
            # Preserve the app's bid-only variant: belote helps fulfill a numeric
            # contract, while the award is the bid (250 for a made capot).
            award = (self.BONUS_CAPOT if requested_capot else bid) if success else 160
            awards[winner] = award * multiplier
        else:
            # FFB Contrée, sections 7 and 10.2: a failed taker's belote transfers
            # even if the first card was announced but rebelote was omitted.
            transferred_bonus = sum(bonuses)
            if not success and bonuses[0] == 0 and self.player_with_belote in sides[0] and (
                    self._belote_started or self.belote_status in (
                        BeloteStatus.Belote_Played, BeloteStatus.Rebelote_Announced)):
                transferred_bonus += self.BELOTE_REBELOTE

            if requested_capot:
                awards[winner] = 2 * self.BONUS_CAPOT * multiplier
                if success and multiplier == 1:
                    awards[0] += bonuses[0]
                    awards[1] = bonuses[1]
                else:
                    awards[winner] += transferred_bonus
            elif multiplier > 1 or not success:
                # Doubled hands award the whole stake to the winning side.
                base = 160
                if self.counting == CountingMethod.POINTS_ACHIEVED_PLUS_BID:
                    base = (self.BONUS_CAPOT if capot[winner] else 160) + bid
                awards[winner] = base * multiplier + transferred_bonus
                if self.counting == CountingMethod.POINTS_ACHIEVED and capot[winner]:
                    # Section 10.2, note 2: an unrequested doubled capot is
                    # 320 + 100, rather than doubling the capot premium.
                    awards[winner] += 100 if multiplier > 1 else 90
            else:
                awards = [self._round_score(total) for total in points]
                if capot[0]:
                    awards[0] = self.BONUS_CAPOT + bonuses[0]
                if self.counting == CountingMethod.POINTS_ACHIEVED_PLUS_BID:
                    awards[0] += bid

        return self._record_hand_scores(sides, points, awards, sides[winner])
