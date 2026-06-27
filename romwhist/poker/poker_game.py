"""
This module implements poker game functionality using the existing card game base.
"""

import logging
from enum import Enum

from romwhist.card import Card
from romwhist.deck import Deck
from romwhist.hand import Hand
from romwhist.game import CardGame
from romwhist.game_state import GameState
from romwhist.player import Player


from collections import Counter


class PokerGame(CardGame):
    MAX_PLAYERS = 6
    HAND_SIZE = 5
    POKER_TYPE_LABELS = {
        "texas_holdem": "Texas Hold'em",
        "omaha": "Omaha",
    }

    class GamePhase(str, Enum):
        DEAL = "Deal"
        PLAY = "Play"
        SHOWDOWN = "Showdown"
        OVER = "Over"

    class PokerHandRank(int, Enum):
        HIGH_CARD = 1
        ONE_PAIR = 2
        TWO_PAIR = 3
        THREE_OF_A_KIND = 4
        STRAIGHT = 5
        FLUSH = 6
        FULL_HOUSE = 7
        FOUR_OF_A_KIND = 8
        STRAIGHT_FLUSH = 9
        ROYAL_FLUSH = 10

    HAND_RANK_LABELS = {
        PokerHandRank.HIGH_CARD: "High Card",
        PokerHandRank.ONE_PAIR: "One Pair",
        PokerHandRank.TWO_PAIR: "Two Pair",
        PokerHandRank.THREE_OF_A_KIND: "Three of a Kind",
        PokerHandRank.STRAIGHT: "Straight",
        PokerHandRank.FLUSH: "Flush",
        PokerHandRank.FULL_HOUSE: "Full House",
        PokerHandRank.FOUR_OF_A_KIND: "Four of a Kind",
        PokerHandRank.STRAIGHT_FLUSH: "Straight Flush",
        PokerHandRank.ROYAL_FLUSH: "Royal Flush",
    }

    def __init__(self, game_creator=None, id=0, poker_type="texas_holdem"):
        CardGame.__init__(self, game_creator=game_creator, deck_size=52, id=id)
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()
        self.hand_size = PokerGame.HAND_SIZE
        self.hand_winners = []
        self.poker_type = poker_type

    def reset(self):
        CardGame.reset(self)
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()
        self.hand_winners = []

    def get_state(self):
        state = GameState(self.id)
        state.poker_type = self.poker_type
        return self.populate_state(state)

    def get_poker_type_label(self):
        return PokerGame.POKER_TYPE_LABELS.get(self.poker_type, self.poker_type)

    def add_player(self, player):
        CardGame.add_player(self, player)

    def start_game(self):
        self._started = True
        self.deck_size = 52
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()
        if self.dealer is None and self.get_playing_players():
            self.dealer = self.get_playing_players()[0]
        self.deal_cards()
        self.phase = PokerGame.GamePhase.SHOWDOWN
        self.active_player = None
        self.hand_winners = self.get_winners()

    def deal_cards(self):
        if self.deck is None:
            self.deck = Deck(self.deck_size)
            self.deck.shuffle()

        self.hands = dict()
        for player in self.get_playing_players():
            self.hands[player] = Hand(self.deck, self.hand_size)
            self.hands[player].sort()

        self.wins = dict()
        self.init_dict(self.wins, 0)
        self.init_dict(self.scores, 0)

    def round_ended(self, winner):
        pass

    def hand_completed(self):
        self.update_scores()
        self._current_hand_nb += 1
        self.phase = PokerGame.GamePhase.OVER

    def update_scores(self):
        for player in self.get_playing_players():
            self.scores[player] = self.scores.get(player, 0) + (1 if player in self.hand_winners else 0)
        return self.scores

    def is_game_over(self):
        return self._current_hand_nb >= 1

    def get_allowed_cards(self, player):
        if self.phase != PokerGame.GamePhase.PLAY:
            return []
        return CardGame.get_allowed_cards(self, player)

    def get_hand_rank(self, player):
        if player not in self.hands:
            return None
        return self.score_hand(self.hands[player])

    def get_winners(self):
        best_score = None
        winners = []
        for player in self.get_playing_players():
            score = self.get_hand_rank(player)
            if best_score is None or score > best_score:
                best_score = score
                winners = [player]
            elif score == best_score:
                winners.append(player)
        return winners

    def score_hand(self, hand):
        cards = sorted(hand.get_cards(), key=lambda c: c.card_num, reverse=True)
        ranks = [card.card_num for card in cards]
        suits = [card.suit_char for card in cards]
        rank_counts = Counter(ranks)
        counts_sorted = sorted(rank_counts.items(), key=lambda item: (-item[1], -item[0]))
        is_flush = len(set(suits)) == 1
        is_straight, straight_high = self._is_straight(ranks)

        if is_straight and is_flush:
            if straight_high == 14:
                return (PokerGame.PokerHandRank.ROYAL_FLUSH, [straight_high])
            return (PokerGame.PokerHandRank.STRAIGHT_FLUSH, [straight_high])

        if counts_sorted[0][1] == 4:
            four_rank = counts_sorted[0][0]
            kicker = [rank for rank in ranks if rank != four_rank]
            return (PokerGame.PokerHandRank.FOUR_OF_A_KIND, [four_rank] + kicker)

        if counts_sorted[0][1] == 3 and counts_sorted[1][1] == 2:
            return (PokerGame.PokerHandRank.FULL_HOUSE, [counts_sorted[0][0], counts_sorted[1][0]])

        if is_flush:
            return (PokerGame.PokerHandRank.FLUSH, ranks)

        if is_straight:
            return (PokerGame.PokerHandRank.STRAIGHT, [straight_high])

        if counts_sorted[0][1] == 3:
            three_rank = counts_sorted[0][0]
            kickers = [rank for rank in ranks if rank != three_rank]
            return (PokerGame.PokerHandRank.THREE_OF_A_KIND, [three_rank] + kickers)

        if counts_sorted[0][1] == 2 and counts_sorted[1][1] == 2:
            pair_ranks = sorted([counts_sorted[0][0], counts_sorted[1][0]], reverse=True)
            kicker = [rank for rank in ranks if rank not in pair_ranks]
            return (PokerGame.PokerHandRank.TWO_PAIR, pair_ranks + kicker)

        if counts_sorted[0][1] == 2:
            pair_rank = counts_sorted[0][0]
            kickers = [rank for rank in ranks if rank != pair_rank]
            return (PokerGame.PokerHandRank.ONE_PAIR, [pair_rank] + kickers)

        return (PokerGame.PokerHandRank.HIGH_CARD, ranks)

    def _is_straight(self, ranks):
        unique = sorted(set(ranks), reverse=True)
        if len(unique) != 5:
            return False, None
        if unique[0] - unique[4] == 4 and all(unique[i] - unique[i + 1] == 1 for i in range(4)):
            return True, unique[0]
        if unique == [14, 5, 4, 3, 2]:
            return True, 5
        return False, None

    def get_hand_rank_description(self, player):
        hand_rank = self.get_hand_rank(player)
        if hand_rank is None:
            return None
        category = hand_rank[0]
        return PokerGame.HAND_RANK_LABELS.get(category, "Unknown")
