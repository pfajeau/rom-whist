"""
This module implements poker game tests.
"""

from romwhist.card import Card
from romwhist.hand import Hand
from romwhist.player import Player
from romwhist.poker.poker_game import PokerGame


def make_hand(card_values):
    hand = Hand(None, 0)
    for card_value in card_values:
        hand.add(Card.card_from_value(card_value))
    hand.sort()
    return hand


def make_game(poker_type):
    game = PokerGame(game_creator="creator", id=1, poker_type=poker_type)
    player = Player("alice")
    game.add_player(player)
    return game, player


def test_texas_holdem_scores_best_five_cards_from_hole_and_board():
    game, player = make_game("texas_holdem")
    game.hands[player] = make_hand(["h14", "s2"])
    game.community_cards = make_hand(["h10", "h11", "h12", "h13", "c9"])

    score = game.get_hand_rank(player)

    assert score[0] == PokerGame.PokerHandRank.ROYAL_FLUSH
    assert game.get_best_hand(player).serialize() == ["h10", "h11", "h12", "h13", "h14"]


def test_omaha_requires_two_hole_cards():
    game, player = make_game("omaha")
    game.hands[player] = make_hand(["h14", "s2", "d3", "c4"])
    game.community_cards = make_hand(["h10", "h11", "h12", "h13", "c9"])

    score = game.get_hand_rank(player)

    assert score[0] == PokerGame.PokerHandRank.HIGH_CARD
    assert game.get_best_hand(player).serialize() == ["c4", "h11", "h12", "h13", "h14"]