"""
This module implements poker game functionality with full Texas Hold'em phases.

Phases: DEAL → PRE_FLOP → FLOP → TURN → RIVER → SHOWDOWN → OVER
Betting: fold, check, call, bet, raise with small/big blind structure.
"""

import logging
from collections import Counter
from enum import Enum
from itertools import combinations

from romwhist.deck import Deck
from romwhist.game import CardGame
from romwhist.game_state import GameState
from romwhist.hand import Hand
from romwhist.player import Player


class PokerGame(CardGame):
    MAX_PLAYERS = 6
    BOARD_SIZE = 5
    HOLE_CARDS_BY_TYPE = {
        "texas_holdem": 2,
        "omaha": 4,
    }
    POKER_TYPE_LABELS = {
        "texas_holdem": "Texas Hold'em",
        "omaha": "Omaha",
    }

    class GamePhase(str, Enum):
        DEAL = "Deal"
        PRE_FLOP = "Pre-Flop"
        FLOP = "Flop"
        TURN = "Turn"
        RIVER = "River"
        SHOWDOWN = "Showdown"
        OVER = "Over"

    # Number of community cards revealed per phase
    COMMUNITY_CARDS_REVEALED = {
        "DEAL": 0, "PRE_FLOP": 0,
        "FLOP": 3, "TURN": 4, "RIVER": 5,
        "SHOWDOWN": 5, "OVER": 5,
    }

    # Ordered betting phases (SHOWDOWN is the final destination)
    PHASE_SEQUENCE = ["PRE_FLOP", "FLOP", "TURN", "RIVER", "SHOWDOWN"]

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

    def __init__(self, game_creator=None, id=0, poker_type="texas_holdem", initial_money=1000):
        CardGame.__init__(self, game_creator=game_creator, deck_size=52, id=id)
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()
        self.poker_type = poker_type if poker_type in PokerGame.HOLE_CARDS_BY_TYPE else "texas_holdem"
        self.hand_size = PokerGame.HOLE_CARDS_BY_TYPE[self.poker_type]
        self.hole_cards_count = self.hand_size
        # community_cards: only the currently-revealed cards (Hand)
        self.community_cards = None
        # _all_community_cards: all 5 dealt at start, revealed progressively
        self._all_community_cards = None
        self.hand_winners = []
        self.initial_money = max(10, min(10000, int(initial_money)))
        self.money = {}
        # Betting state
        self.pot = 0
        self.current_bet = 0           # highest bet placed this round
        self.bets_this_round = {}      # player -> amount bet in current round
        self.folded_players = []       # players who have folded this hand
        self._to_act = []              # players who still need to act this round
        self.small_blind = max(1, self.initial_money // 100)
        self.big_blind = self.small_blind * 2

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def reset(self):
        CardGame.reset(self)
        self.deck = Deck(self.deck_size)
        self.deck.shuffle()
        self.community_cards = None
        self._all_community_cards = None
        self.hand_winners = []
        self.pot = 0
        self.current_bet = 0
        self.bets_this_round = {}
        self.folded_players = []
        self._to_act = []

    def add_player(self, player):
        CardGame.add_player(self, player)
        self.money[player] = self.initial_money

    def get_money(self):
        return self.money

    # ------------------------------------------------------------------
    # State serialisation
    # ------------------------------------------------------------------

    def get_state(self):
        state = GameState(self.id)
        state.poker_type = self.poker_type
        state.hole_cards_count = self.hole_cards_count
        state.community_cards = self.community_cards.serialize() if self.community_cards is not None else []
        state.pot = self.pot
        state.current_bet = self.current_bet
        state.bets_this_round = {str(k): v for k, v in self.bets_this_round.items()}
        state.folded_players = [str(p) for p in self.folded_players]
        state.money = {str(k): v for k, v in self.money.items()}
        state.small_blind = self.small_blind
        state.big_blind = self.big_blind
        return self.populate_state(state)

    def get_poker_type_label(self):
        return PokerGame.POKER_TYPE_LABELS.get(self.poker_type, self.poker_type)

    # ------------------------------------------------------------------
    # Active-player helpers
    # ------------------------------------------------------------------

    def get_solvent_players(self):
        """Players who still have money and can participate in the next hand."""
        return [p for p in self.get_playing_players() if self.money.get(p, 0) > 0]

    def get_active_players(self):
        """Players who have not folded this hand."""
        return [p for p in self.get_playing_players() if p not in self.folded_players]

    def get_allowed_actions(self, player=None):
        """Fold / check / call / bet / raise for the given player."""
        if player is None:
            player = self.active_player
        if player is None:
            return []
        if self.phase in (PokerGame.GamePhase.DEAL,
                          PokerGame.GamePhase.SHOWDOWN,
                          PokerGame.GamePhase.OVER):
            return []
        if player not in self.get_active_players():
            return []
        if self.active_player != player:
            return []

        player_bet = self.bets_this_round.get(player, 0)
        player_money = self.money.get(player, 0)
        actions = ['fold']

        if player_bet >= self.current_bet:
            actions.append('check')
        else:
            actions.append('call')

        if player_money > 0:
            if self.current_bet == 0 or player_bet >= self.current_bet:
                actions.append('bet')
            else:
                actions.append('raise')

        return actions

    # ------------------------------------------------------------------
    # Game start / dealing
    # ------------------------------------------------------------------

    def start_game(self):
        self._started = True
        # Only deal to players who still have money
        players = self.get_solvent_players()
        if not players:
            return

        self.deck = Deck(52)
        self.deck.shuffle()

        # Rotate dealer among solvent players
        if self.dealer is None or self.dealer not in players:
            self.dealer = players[0]
        else:
            idx = players.index(self.dealer)
            self.dealer = players[(idx + 1) % len(players)]

        # Reset hand-level state
        self.pot = 0
        self.current_bet = 0
        self.bets_this_round = {p: 0 for p in players}
        self.folded_players = []
        self.hand_winners = []
        self.wins = {p: 0 for p in players}
        self.init_dict(self.scores, 0)

        # Deal hole cards
        self.hands = {}
        for player in players:
            self.hands[player] = Hand(self.deck, self.hole_cards_count)
            self.hands[player].sort()

        # Deal all 5 community cards at once (revealed progressively)
        self._all_community_cards = Hand(self.deck, PokerGame.BOARD_SIZE)
        self.community_cards = Hand(None, 0)
        self.community_cards.cards = []

        # Post blinds
        n = len(players)
        dealer_idx = players.index(self.dealer)
        if n == 2:
            # Heads-up: dealer = SB, other = BB; SB acts first pre-flop
            sb_idx = dealer_idx
            bb_idx = (dealer_idx + 1) % n
            utg_idx = dealer_idx
        else:
            sb_idx = (dealer_idx + 1) % n
            bb_idx = (dealer_idx + 2) % n
            utg_idx = (dealer_idx + 3) % n

        self._post_forced_bet(players[sb_idx], self.small_blind)
        self._post_forced_bet(players[bb_idx], self.big_blind)
        self.current_bet = self.big_blind

        # PRE_FLOP: UTG acts first
        self.phase = PokerGame.GamePhase.PRE_FLOP
        self._init_betting_order(players[utg_idx % len(players)])

    def _post_forced_bet(self, player, amount):
        actual = min(amount, self.money.get(player, 0))
        self.money[player] = self.money.get(player, 0) - actual
        self.bets_this_round[player] = self.bets_this_round.get(player, 0) + actual
        self.pot += actual

    def _init_betting_order(self, start_from):
        """Build the _to_act queue starting from start_from."""
        active = self.get_active_players()
        if not active:
            self._to_act = []
            self.active_player = None
            return
        idx = active.index(start_from) if start_from in active else 0
        ordered = active[idx:] + active[:idx]
        self._to_act = list(ordered)
        self.active_player = self._to_act[0]

    # ------------------------------------------------------------------
    # Betting actions
    # ------------------------------------------------------------------

    def player_action(self, player, action, amount=0):
        """Process fold/check/call/bet/raise. Returns True on success."""
        if self.active_player != player:
            return False
        allowed = self.get_allowed_actions(player)
        if action not in allowed:
            return False

        player_bet = self.bets_this_round.get(player, 0)
        player_money = self.money.get(player, 0)

        if action == 'fold':
            self.folded_players.append(player)
            if player in self._to_act:
                self._to_act.remove(player)

        elif action == 'check':
            if player in self._to_act:
                self._to_act.remove(player)

        elif action == 'call':
            to_call = min(self.current_bet - player_bet, player_money)
            self.money[player] -= to_call
            self.bets_this_round[player] = player_bet + to_call
            self.pot += to_call
            if player in self._to_act:
                self._to_act.remove(player)

        elif action in ('bet', 'raise'):
            amount = max(self.big_blind, int(amount))
            total_target = (self.current_bet + amount) if action == 'raise' else amount
            to_add = min(total_target - player_bet, player_money)
            if to_add <= 0:
                return False
            self.money[player] -= to_add
            self.bets_this_round[player] = player_bet + to_add
            self.pot += to_add
            self.current_bet = self.bets_this_round[player]
            # Everyone else must act again
            self._to_act = [p for p in self.get_active_players() if p != player]

        else:
            return False

        # Advance to next player
        self.active_player = self._to_act[0] if self._to_act else None
        return True

    def is_betting_round_complete(self):
        return len(self._to_act) == 0 or len(self.get_active_players()) <= 1

    # ------------------------------------------------------------------
    # Phase progression
    # ------------------------------------------------------------------

    def _reveal_community_cards(self):
        n = PokerGame.COMMUNITY_CARDS_REVEALED.get(self.phase.name, 0)
        all_cards = self._all_community_cards.get_cards() if self._all_community_cards else []
        self.community_cards = Hand(None, 0)
        self.community_cards.cards = list(all_cards[:n])

    def advance_phase(self):
        """Move to the next phase. Returns the new GamePhase."""
        active = self.get_active_players()
        if len(active) <= 1:
            # Everyone else folded — skip straight to showdown
            self.phase = PokerGame.GamePhase.SHOWDOWN
        else:
            seq = PokerGame.PHASE_SEQUENCE
            idx = seq.index(self.phase.name) if self.phase.name in seq else -1
            next_name = seq[idx + 1] if idx < len(seq) - 1 else "SHOWDOWN"
            self.phase = PokerGame.GamePhase[next_name]

        self._reveal_community_cards()

        if self.phase == PokerGame.GamePhase.SHOWDOWN:
            self.hand_winners = self.get_winners()
            self._award_pot()
            self.active_player = None
            self._to_act = []
        else:
            # Start a fresh betting round from the player after the dealer
            players = self.get_playing_players()
            self.current_bet = 0
            self.bets_this_round = {p: 0 for p in players}
            active = self.get_active_players()
            if active:
                d_idx = active.index(self.dealer) if self.dealer in active else 0
                start = active[(d_idx + 1) % len(active)]
                self._init_betting_order(start)

        return self.phase

    def _award_pot(self):
        if not self.hand_winners:
            return
        share = self.pot // len(self.hand_winners)
        remainder = self.pot % len(self.hand_winners)
        for i, winner in enumerate(self.hand_winners):
            self.money[winner] = self.money.get(winner, 0) + share + (remainder if i == 0 else 0)
        self.pot = 0

    def hand_completed(self):
        self._current_hand_nb += 1
        self.phase = PokerGame.GamePhase.OVER

    def is_game_over(self):
        """True when only one player still has money."""
        return len(self.get_solvent_players()) <= 1

    # ------------------------------------------------------------------
    # Winner determination
    # ------------------------------------------------------------------

    def get_winners(self):
        """Best hand among active (non-folded) players."""
        candidates = self.get_active_players()
        if not candidates:
            return self.get_playing_players()[:1]
        if len(candidates) == 1:
            return candidates
        best_score = None
        winners = []
        for player in candidates:
            score = self.get_hand_rank(player)
            if score is None:
                continue
            if best_score is None or score > best_score:
                best_score = score
                winners = [player]
            elif score == best_score:
                winners.append(player)
        return winners

    def get_hand_rank(self, player):
        if player not in self.hands or self._all_community_cards is None:
            return None
        # Use all 5 community cards for evaluation (even if not all revealed)
        saved = self.community_cards
        full = Hand(None, 0)
        full.cards = list(self._all_community_cards.get_cards())
        self.community_cards = full
        best_score, _ = self._best_score_for_player(player)
        self.community_cards = saved
        return best_score

    def get_best_hand(self, player):
        if player not in self.hands or self._all_community_cards is None:
            return None
        saved = self.community_cards
        full = Hand(None, 0)
        full.cards = list(self._all_community_cards.get_cards())
        self.community_cards = full
        _, best_cards = self._best_score_for_player(player)
        self.community_cards = saved
        if best_cards is None:
            return None
        hand = Hand(None, 0)
        hand.cards = list(best_cards)
        hand.sort()
        return hand

    def get_hand_rank_description(self, player):
        hand_rank = self.get_hand_rank(player)
        if hand_rank is None:
            return None
        return PokerGame.HAND_RANK_LABELS.get(hand_rank[0], "Unknown")

    # ------------------------------------------------------------------
    # Card evaluation (unchanged)
    # ------------------------------------------------------------------

    def score_hand(self, hand):
        cards = hand.get_cards() if hasattr(hand, "get_cards") else list(hand)
        return self._score_five_card_hand(cards)

    def _score_five_card_hand(self, cards):
        cards = sorted(cards, key=lambda c: c.card_num, reverse=True)
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

    def _best_score_for_player(self, player):
        hole_cards = self.hands[player].get_cards()
        board_cards = self.community_cards.get_cards() if self.community_cards is not None else []
        best_score = None
        best_cards = None

        if self.poker_type == "omaha":
            if len(hole_cards) < 2 or len(board_cards) < 3:
                return None, None
            for hole_combo in combinations(hole_cards, 2):
                for board_combo in combinations(board_cards, 3):
                    current_cards = list(hole_combo) + list(board_combo)
                    score = self._score_five_card_hand(current_cards)
                    if best_score is None or score > best_score:
                        best_score = score
                        best_cards = current_cards
        else:
            available_cards = list(hole_cards) + list(board_cards)
            if len(available_cards) < 5:
                return None, None
            for current_cards in combinations(available_cards, 5):
                current_cards = list(current_cards)
                score = self._score_five_card_hand(current_cards)
                if best_score is None or score > best_score:
                    best_score = score
                    best_cards = current_cards

        return best_score, best_cards

    def _is_straight(self, ranks):
        unique = sorted(set(ranks), reverse=True)
        if len(unique) != 5:
            return False, None
        if unique[0] - unique[4] == 4 and all(unique[i] - unique[i + 1] == 1 for i in range(4)):
            return True, unique[0]
        if unique == [14, 5, 4, 3, 2]:
            return True, 5
        return False, None

    # kept for backward compat with any AI code
    def get_allowed_cards(self, player):
        return []

    def round_ended(self, winner):
        pass
