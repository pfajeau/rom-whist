"""
This module implements belote functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import copy
import logging
from enum import Enum
from flask_babel import gettext as _

from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.hand import Hand
from romwhist.game import CardGame
from romwhist.player import Player
from romwhist.belote.belote_state import BeloteState
from romwhist.belote.belote_status import BeloteStatus


class BeloteGame(CardGame):
    TOTAL_POINTS = 162
    MAX_PLAYERS = 4
    # Contrée permits discarding when an opponent cannot be overtrumped.
    MUST_UNDERTRUMP = True

    class GamePhase(str, Enum):
        DEAL = "Deal"
        DEAL2 = "Deal2"
        BET = "Bet"
        BET2 = "Bet2"
        PLAY = "Play"
        OVER = "Over"

    class BeloteAnnounced(str, Enum):
        BELOTE = "belote"
        REBELOTE = "rebelote"

    def __init__(self, game_creator=None, id=0):
        CardGame.__init__(self, game_creator=game_creator, deck_size=0, id=id)
        self.taker = None
        self.teams = []
        # self.__belote_announced = BeloteGame.BeloteAnnounced.No
        self.__belote_status = BeloteStatus.Not_Allowed
        self.__player_with_belote = None
        self.__bonus_litige = 0
        self.__win_game_points = 1000
        self.init_dict(self.hand_points, 0)
        self._hand_winner = []
        self.deck = None
        self._nb_pass_since_bet = 0
        self._hand_scored = False
        self._belote_started = False

        self.reset_card_ranks_and_points()

        # Number of cards to deal depending on number of players
        self.nb_cards_first_deal = {1: 6, 2: 6, 3: 6, 4: 5}
        self.nb_cards_second_deal = {1: 3, 2: 3, 3: 3, 4: 3}

        # Total number of points
        self.TOTAL_POINTS = BeloteGame.TOTAL_POINTS
        self.BONUS_CAPOT = 100
        self.DIX_DE_DER = 10
        self.BELOTE_REBELOTE = 20

    def reset_card_ranks_and_points(self):
        # Points and ranks will change for the trump suit once it is known
        self.card_points = {"c7": 0, "c8": 0, "c9": 0, "c10": 10, "c11": 2, "c12": 3, "c13": 4, "c14": 11,
                            "d7": 0, "d8": 0, "d9": 0, "d10": 10, "d11": 2, "d12": 3, "d13": 4, "d14": 11,
                            "h7": 0, "h8": 0, "h9": 0, "h10": 10, "h11": 2, "h12": 3, "h13": 4, "h14": 11,
                            "s7": 0, "s8": 0, "s9": 0, "s10": 10, "s11": 2, "s12": 3, "s13": 4, "s14": 11}

        self.card_ranks = {"c7": 7, "c8": 8, "c9": 9, "c10": 13, "c11": 10, "c12": 11, "c13": 12, "c14": 14,
                           "d7": 7, "d8": 8, "d9": 9, "d10": 13, "d11": 10, "d12": 11, "d13": 12, "d14": 14,
                           "h7": 7, "h8": 8, "h9": 9, "h10": 13, "h11": 10, "h12": 11, "h13": 12, "h14": 14,
                           "s7": 7, "s8": 8, "s9": 9, "s10": 13, "s11": 10, "s12": 11, "s13": 12, "s14": 14}

        self.ranks_trump = {7: 7, 8: 8, 9: 13, 10: 11, 11: 14, 12: 9, 13: 10, 14: 12}

    @property
    def hand_winner(self):
        return self._hand_winner

    @property
    def bonus_litige(self):
        return self.__bonus_litige

    @bonus_litige.setter
    def bonus_litige(self, value):
        self.__bonus_litige = value

    @property
    def player_with_belote(self):
        return self.__player_with_belote

    @player_with_belote.setter
    def player_with_belote(self, value):
        self.__player_with_belote = value

    @property
    def belote_status(self):
        return self.__belote_status

    @belote_status.setter
    def belote_status(self, value):
        self.__belote_status = value

    @property
    def win_game_points(self):
        return self.__win_game_points

    @win_game_points.setter
    def win_game_points(self, value):
        self.__win_game_points = value

    def get_state(self):
        state = BeloteState(self.id)
        new_state = self.populate_state(state)
        return new_state

    def populate_state(self, state):
        my_state = CardGame.populate_state(self, state)
        my_state.allowed_bets = self.get_allowed_bets(self.active_player)
        my_state.phase = self.phase
        my_state.hand_winner = copy.deepcopy(self.hand_winner)
        my_state.taker = self.taker
        if self.taker is not None:
            my_state.taker = str(self.taker)
        my_state.belote_status = self.belote_status
        my_state.player_with_belote = str(self.player_with_belote) if self.player_with_belote is not None else None
        my_state.nb_rounds_won = {str(player): wins for player, wins in self.wins.items()}
        my_state.bonus_litige = self.bonus_litige
        my_state.win_game_points = self.win_game_points
        my_state.hand_scored = self._hand_scored
        my_state.belote_started = self._belote_started
        my_state.round_leaders = {str(index): str(game_round.first_player)
                                 for index, game_round in enumerate(self.rounds)
                                 if game_round.round_started}
        return my_state

    def populate_from_state(self, state):
        CardGame.populate_from_state(self, state)
        self.soft_init_dict(self.wins, 0)
        self.soft_init_dict(self.bets, "")
        self.phase = state.phase
        self.soft_init_dict(self.hand_points, 0)

        self._hand_winner = [self.get_player_by_name(player) if player else ""
                            for player in state.hand_winner]
        if state.taker is not None:
            self.taker = Player(state.taker)

        self.belote_status = BeloteStatus(state.belote_status)
        self.player_with_belote = self.get_player_by_name(state.player_with_belote)
        self.bonus_litige = state.bonus_litige
        self.win_game_points = state.win_game_points
        self._hand_scored = state.hand_scored
        self._belote_started = state.belote_started
        if self.trump_suit in Card.SUIT_NAMES:
            self.set_cards_rank_and_value()
        leader = self.next_player(self.dealer)
        for index, game_round in enumerate(self.rounds):
            if state.round_leaders is not None:
                name = state.round_leaders.get(str(index))
                if name is not None:
                    leader = self.get_player_by_name(name)
            if game_round.cards_played.get(leader) is not None:
                game_round.first_player = leader
                game_round.first_card_played = game_round.cards_played[leader]
                if game_round.last_card_played():
                    leader = game_round.compute_winner()
        if state.nb_rounds_won is not None:
            for player in self.players:
                self.wins[player] = state.nb_rounds_won.get(str(player), 0)
        else:
            # Older snapshots did not include trick counts.
            for game_round in self.rounds:
                if game_round.last_card_played():
                    self.wins[game_round.compute_winner()] += 1

    def player_announced_belote(self, player, value):
        # check player can announce (has the right cards and belote_state ha the right value)
        logging.debug("In player_announced_belote, value is: " + str(value))
        logging.debug("Belote state value: " + self.belote_status.name)
        if player != self.player_with_belote or self.phase != self.GamePhase.PLAY:
            return self.belote_status
        if value == self.BeloteAnnounced.BELOTE:

            belote_ok = self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "12") and \
                        self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "13") and \
                        self.belote_status == BeloteStatus.Allowed
            if belote_ok:
                self.belote_status = BeloteStatus.Belote_Announced
        elif value == self.BeloteAnnounced.REBELOTE:
            belote_ok = (self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "12") or
                         self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "13")) and \
                        self.belote_status == BeloteStatus.Belote_Played
            if belote_ok:
                self.belote_status = BeloteStatus.Rebelote_Announced
        logging.debug("Belote state value: " + self.belote_status.name)
        return self.belote_status

    def has_player_card(self, player, card_as_str):
        for card in self.hands[player].cards:
            if str(card) == card_as_str:
                return True
        return False

    def reset(self):
        CardGame.reset(self)
        self.taker = None
        self.belote_status = BeloteStatus.Not_Allowed
        self.player_with_belote = None
        self.bonus_litige = 0
        self._hand_winner = []
        self._hand_scored = False
        self._belote_started = False

    def is_game_over(self):
        # Partners share a score; only compare one representative per team.
        competitors = self.players[:2] if len(self.players) == 4 else self.players
        totals = [self.scores[player] for player in competitors]
        if not totals:
            return False
        highest = max(totals)
        return highest >= self.win_game_points and totals.count(highest) == 1

    def add_player(self, player):
        CardGame.add_player(self, player)
        self.hand_points[player] = 0

    def disable_player(self, player):
        logging.info("In BeloteGame.disable_player, disabling player " + player)
        CardGame.disable_player(self, player)
        if player in self.players:
            self.phase = BeloteGame.GamePhase.DEAL

    def start_game(self):
        self._started = True
        self.deck_size = 32
        self.phase = BeloteGame.GamePhase.BET

    def place_bet(self, player, bet, ai=False):
        logging.info("Player " + player + "bid: " + bet)
        self.bets[player] = bet

        if bet == "pass":
            logging.info("Player passed")
            self._nb_pass_since_bet += 1

            # Ask next player
            self.active_player = self.next_player(player)
            if self.next_player_to_bet(player) is None:
                self.init_bets()
                if self.phase == BeloteGame.GamePhase.BET:
                    logging.debug("Moving to second round of betting")
                    self._nb_pass_since_bet = 0
                    self.phase = BeloteGame.GamePhase.BET2
                else:
                    logging.debug("Everybody has passed twice")
                    # BET2 phase, and nobody has taken
                    self.phase = BeloteGame.GamePhase.DEAL
                    self.dealer = self.next_player_to_deal()
        else:
            logging.info("Player took")
            self.phase = BeloteGame.GamePhase.PLAY
            self.trump_suit = bet
            self.taker = player

            # Note: this is also done in deal_2, so may be redundant
            self.set_cards_rank_and_value()
            
            self.active_player = self.next_player(self.dealer)

        return
    
    # Return None if all players have bet
    def next_player_to_bet(self, player, no_bet_string=""):
        logging.debug("Next player to bet after: " + player)
        next_player = self.next_player(player)
        if str(self.bets[next_player]) == no_bet_string or self._nb_pass_since_bet < len(self.players) - 1:
            logging.debug("Next player to bet after " + player + " is: " + next_player)
            return next_player
        else:
            logging.debug("No more player to bet")
            return None

    def get_allowed_bets(self, player):
        allowed_bets = []
        # if self.hands.get(player) is None:
        #     allowed_bets = []  # No hand yet
        if self.phase == self.GamePhase.BET:
            allowed_bets = ['pass', str(self.trump_card.get_suit_name())]
        elif self.phase == self.GamePhase.BET2:
            allowed_bets = ['pass']
            for suit in Card.SUIT_NAMES:
                if suit != self.trump_card.get_suit_name():
                    allowed_bets.append(suit)

        logging.debug("allowed bets:" + str(allowed_bets))
        return allowed_bets

    # Return list of allowed cards as a list of
    # cards represented as string (e.g. 'c4')
    def get_allowed_cards(self, player):
        # Allowed cards are cars of the same suit than the first card played
        # If no cards are of the same suit, trump cards must be played. If no trump card
        # any card is allowed
        allowed_cards = []
        if player is None or player not in self.hands:
            return allowed_cards
        if self.current_round is None:
            logging.debug("Current round is None")
            return allowed_cards
        if self.current_round.get_first_card_played() is None:
            # Round is just starting, all cards are allowed
            allowed_cards = self.get_hand(player).serialize()
        else:
            asked_suit = self.current_round.get_first_card_played().get_suit_name()
            winning_player = self.current_round.winning_player_for_suit(asked_suit)
            winning_card = self.current_round.cards_played[winning_player]
            trump_asked = (asked_suit == self.trump_suit)
            lower_trumps = []
            higher_trump = False
            logging.debug("Player %s hand is: %s ", player, self.hands[player].serialize())
            logging.debug("Asked suit is %s", asked_suit)
            logging.debug("Trump suit is  %s", self.trump_suit)
            for card in self.hands[player].get_cards():
                if card.get_suit_name() == asked_suit:
                    if trump_asked:
                        if card > winning_card:
                            # Only allow cards higher than already played trump
                            allowed_cards.append(str(card))
                            higher_trump = True
                        else:
                            lower_trumps.append(str(card))
                    else:
                        allowed_cards.append(str(card))

            # Allow smaller trumps if no higher trump
            if not higher_trump and len(lower_trumps) > 0:
                allowed_cards = lower_trumps

            # If player has trump, must play it unless partner has already cut or
            # partner played strongest card.
            # Also need to surcouper if applicable
            if len(allowed_cards) == 0:
                cut = (winning_card.get_suit_name() == self.trump_suit)
                for card in self.hands[player].cards:
                    # Check for trump cards
                    if card.get_suit_name() == self.trump_suit:
                        if not cut:
                            # if partner has highest card, do not have to cut
                            if len(self.players) == 4 and winning_player == self.next_player(self.next_player(player)):
                                return self.hands[player].serialize()
                            else:
                                # Else has to play trump
                                allowed_cards.append(str(card))
                        else:
                            # Somebody has cut already
                            if len(self.players) != 4:
                                if card > winning_card:
                                    # Only allow cards higher than already played trump
                                    allowed_cards.append(str(card))
                                    higher_trump = True
                                else:
                                    lower_trumps.append(str(card))
                            else:
                                # 4 players
                                if winning_player == self.next_player(self.next_player(player)):
                                    return self.hands[player].serialize()
                                else:
                                    if card > winning_card:
                                        # Only allow cards higher than already played trump
                                        allowed_cards.append(str(card))
                                        higher_trump = True
                                    else:
                                        lower_trumps.append(str(card))

                if not higher_trump and len(lower_trumps) > 0:
                    if self.MUST_UNDERTRUMP:
                        allowed_cards = lower_trumps
                    else:
                        return self.hands[player].serialize()

            # Any card is allowed if no asked suit and no trump
            if len(allowed_cards) == 0:
                allowed_cards = self.hands[player].serialize()

        # TODO: user has to surcouper if they can

        return allowed_cards

    def _scoring_sides(self):
        """Return the takers first, followed by the opposing side(s)."""
        ordered = [self.taker]
        for _ in range(1, len(self.players)):
            ordered.append(self.next_player(ordered[-1]))
        if len(ordered) == 4:
            return [ordered[::2], ordered[1::2]]
        return [[player] for player in ordered]

    def _belote_bonus(self, side):
        if self.belote_status == BeloteStatus.Rebelote_Played and self.player_with_belote in side:
            return self.BELOTE_REBELOTE
        return 0

    def _record_hand_scores(self, sides, points, awards, winners):
        """Publish team hand totals only after all calculations use individual points."""
        self._hand_winner = winners
        for side, total, award in zip(sides, points, awards):
            score = self.scores[side[0]] + award
            for player in side:
                self.hand_points[player] = total
                self.scores[player] = score
        self._hand_scored = True
        self.scoresheet.append(self.scores.copy())
        return self.scores

    def update_scores(self):
        if self._hand_scored:
            return self.scores
        sides = self._scoring_sides()
        raw_points = [sum(self.hand_points[player] for player in side) for side in sides]
        bonuses = [self._belote_bonus(side) for side in sides]
        points = [raw + bonus for raw, bonus in zip(raw_points, bonuses)]
        tricks = [sum(self.wins[player] for player in side) for side in sides]
        if len(sides) == 1:
            return self._record_hand_scores(sides, points, [0], [])
        if len(sides) == 3:
            return self._score_three_players(sides, points, bonuses, tricks)

        if points[0] > points[1]:
            awards = [points[0] + self.bonus_litige, points[1]]
            winners = sides[0]
            self.bonus_litige = 0
        elif points[0] < points[1]:
            # A completed belote stays with its owner, even on a failed contract.
            awards = [bonuses[0], sum(raw_points) + bonuses[1] + self.bonus_litige]
            winners = sides[1]
            self.bonus_litige = 0
        else:
            # The defense scores now; the takers' entire team total is carried.
            awards = [0, points[1]]
            self.bonus_litige += points[0]
            winners = [""]

        for index in range(2):
            if tricks[index] > 0 and tricks[1 - index] == 0:
                awards[index] += self.BONUS_CAPOT - self.DIX_DE_DER
        return self._record_hand_scores(sides, points, awards, winners)

    def _score_three_players(self, sides, points, bonuses, tricks):
        """Keep the existing three-player variant's individual scoring."""
        if points[0] > points[1] and points[0] > points[2]:
            awards = points.copy()
            winners = sides[0]
        elif points[1] > points[2]:
            awards = [bonuses[0], points[1] + points[0] - bonuses[0], points[2]]
            winners = sides[1]
        elif points[2] > points[1]:
            awards = [bonuses[0], points[1], points[2] + points[0] - bonuses[0]]
            winners = sides[2]
        else:
            share = (points[0] - bonuses[0]) / 2
            awards = [bonuses[0], points[1] + share, points[2] + share]
            winners = []

        for index in range(3):
            if tricks[index] == 0:
                opponents = [other for other in range(3) if other != index and tricks[other] > 0]
                for other in opponents:
                    awards[other] += self.BONUS_CAPOT / len(opponents)
        return self._record_hand_scores(sides, points, awards, winners)

    # Initial deal
    def deal(self, dealer=None):
        hands = self.deal_cards(self.nb_cards_first_deal[len(self.players)], dealer=dealer)
        # Pick up trump card
        self.trump_card = self.deck.deal()
        return hands

    def deal_cards(self, nb_cards, dealer=None):
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()
        self.init_bets()
        self.init_dict(self.wins, 0)
        self.init_dict(self.hand_points, 0)
        self.trump_suit = None
        self.rounds = []
        self._nb_pass_since_bet = 0
        self._hand_scored = False
        self._belote_started = False

        # Reset belote/rebelote states
        self.belote_status = BeloteStatus.Not_Allowed
        # self.BeloteAnnounced = BeloteGame.BeloteAnnounced.No
        self.__player_with_belote = None

        if dealer == None:
            self.dealer = self.active_player
        else:
            self.dealer = dealer

        self.active_player = self.next_player(self.dealer)

        # Create a hand with nb_cards for each player
        for player in self.get_playing_players():
            hand = Hand(self.deck, nb_cards, player)
            self.hands[player] = hand.sort()
            logging.debug("Hand for player " + player + " : " + str(hand.serialize()))

        # Pick up trump card
        self.phase = BeloteGame.GamePhase.BET
        return self.hands

    # Distribute 3 cards for each player
    def deal_2(self, dealer=""):
        logging.debug("In deal_2")

        nb_cards = self.nb_cards_second_deal[len(self.players)]

        # Taker takes the top card then two more
        self.hands[self.taker].add(self.trump_card)
        for i in range(nb_cards - 1):
            self.hands[self.taker].add(self.deck.deal())
        self.hands[self.taker].sort()

        # Other players take 3 cards
        for player in self.get_playing_players():
            if player != self.taker:
                for i in range(nb_cards):
                    self.hands[player].add(self.deck.deal())
                self.hands[player].sort()

        self.update_belote_status()

        # Required to make sure the trump card  is also update properly
        self.set_cards_rank_and_value()

        return self.hands

    def update_belote_status(self):
        # Determine whether Belote / Rebelote enabled for each player
        self.belote_status = BeloteStatus.Not_Allowed
        self.player_with_belote = None
        self._belote_started = False
        for player in self.get_playing_players():
            queen = False
            king = False
            if self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "12"):
                queen = True
            if self.has_player_card(player, Card.get_suit_initial(self.trump_suit) + "13"):
                king = True
            if queen and king:
                logging.info("Player " + player + " can announce belote/re-belote")
                self.belote_status = BeloteStatus.Allowed
                self.player_with_belote = player
                break
        return

    def play_card(self, player, card_value):
        winner = CardGame.play_card(self, player, card_value)
        if self.is_hand_completed():
            # Add 10 points to the winner of the last round
            self.hand_points[winner] += 10

        # Check whether belote / rebelote card played
        # logging.debug ("In Belote.card_played, belote_state is: " + self.belote_state.name)
        belote_card_played = (card_value == Card.get_suit_initial(self.trump_suit) + "12" or
                              card_value == Card.get_suit_initial(self.trump_suit) + "13")

        if belote_card_played and self.belote_status != BeloteStatus.Not_Allowed:
            if self.belote_status == BeloteStatus.Belote_Announced:
                self.belote_status = BeloteStatus.Belote_Played
                self._belote_started = True
                logging.debug("Player " + player + " played belote card: " + card_value)

            elif self.belote_status == BeloteStatus.Rebelote_Announced:
                self.belote_status = BeloteStatus.Rebelote_Played
                logging.debug("Player " + player + " played re-belote card: " + card_value)

            elif self.belote_status == BeloteStatus.Allowed or \
                    self.belote_status == BeloteStatus.Belote_Played:
                # Player lost the points if it was played but not announced
                self.belote_status = BeloteStatus.Lost
                logging.debug("Player " + player + " lost the belote/rebelote points")

        return winner

    def round_ended(self, winner):
        points = self.points_for_round( self.current_round)
        self.hand_points[winner] += points
        return

    def points_for_round(self, round):
        player_cards = round.cards_played
        points = 0
        for player in player_cards:
            card = str(player_cards[player])
            points = points + self.card_points[card]
        logging.debug("Points in round:" + str(points))
        return points

    def hand_completed(self):
        CardGame.hand_completed(self)
        self.belote_status = BeloteStatus.Not_Allowed
        # TODO: check if score threshold has been reached
        # and set game state to OVER if it as

    def set_cards_rank_and_value(self):
        self.reset_card_ranks_and_points()

        suit_trump = Card.get_suit_initial(self.trump_suit)
        self.card_points[suit_trump + "9"] = 14
        self.card_points[suit_trump + "11"] = 20

        for i in range(7, 15):
            self.card_ranks[suit_trump + str(i)] = self.ranks_trump[i]

        for player in self.players:
            for card in self.get_hands()[player].cards:
                card.rank = self.card_ranks[str(card)]
                card.points = self.card_points[str(card)]

        for card in self.deck.cards:
            card.rank = self.card_ranks[str(card)]
            card.points = self.card_points[str(card)]

        if self.current_round is not None:
            for card in self.current_round.cards_played.values():
                if card is not None:
                    card.rank = self.card_ranks[str(card)]
                    card.points = self.card_points[str(card)]

    def init_bet(self, player):
        self.bets[player] = ""

    def init_bets(self):
        self.init_dict(self.bets, "")
