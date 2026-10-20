"""Scoring regressions using the FFB Belote and Contrée rules (§§7–10).

POINTS_BID is the app's existing variant; its capot award is 250.
The two achieved-points modes use the FFB Contrée scoring table.
"""

import json

import pytest

from romwhist import app
from romwhist.belote.belote import BeloteGame
from romwhist.belote.belote_sim import BeloteSim
from romwhist.belote.belote_state import BeloteState
from romwhist.belote.belote_status import BeloteStatus
from romwhist.card import Card
from romwhist.contree.announce import Announce, ContreStatus
from romwhist.contree.contree import ContreeGame, CountingMethod
from romwhist.contree.contree_sim import ContreeSim
from romwhist.contree.contree_state import ContreeState
from romwhist.hand import Hand
from romwhist.player import Player


@pytest.fixture(autouse=True)
def application_context():
    with app.app_context():
        yield


def make_game(game_type=BeloteGame, points=(30, 50, 30, 52), *,
              counting=CountingMethod.POINTS_ACHIEVED, bid=100,
              status=BeloteStatus.Not_Allowed, holder=None, wins=(2, 2, 2, 2)):
    game = (game_type(Player('A'), counting=counting)
            if game_type is ContreeGame else game_type(Player('A')))
    for name in 'ABCD':
        game.add_player(Player(name))
    game.start_game()
    game.deal(dealer=game.players[-1])
    game.phase = game.GamePhase.PLAY
    game.taker = game.players[0]
    game.trump_suit = 'spade'
    game.hand_points.update(zip(game.players, points))
    game.wins.update(zip(game.players, wins))
    game.belote_status = status
    game.player_with_belote = holder
    if game_type is ContreeGame:
        game.current_bet = Announce('spade', bid)
        game.bets[game.taker] = game.current_bet
    return game


def assert_scores(game, takers, defense):
    game.update_scores()
    assert [game.scores[name] for name in 'ABCD'] == [takers, defense, takers, defense]


@pytest.mark.parametrize('status', list(BeloteStatus))
@pytest.mark.parametrize('holder', list('ABCD'))
def test_classic_failed_contract_only_awards_completed_belote(status, holder):
    game = make_game(status=status, holder=holder)
    complete = status == BeloteStatus.Rebelote_Played
    assert_scores(game, 20 if complete and holder in 'AC' else 0,
                  182 if complete and holder in 'BD' else 162)


@pytest.mark.parametrize('holder,expected', [('A', (120, 62)), ('C', (120, 62)),
                                            ('B', (100, 82)), ('D', (100, 82))])
def test_classic_successful_contract_awards_both_teams(holder, expected):
    game = make_game(points=(60, 30, 40, 32), holder=holder,
                     status=BeloteStatus.Rebelote_Played)
    assert_scores(game, *expected)


def test_classic_belote_can_save_or_defeat_contract():
    assert_scores(make_game(points=(40, 40, 32, 50), holder='C',
                            status=BeloteStatus.Rebelote_Played), 92, 90)
    assert_scores(make_game(points=(40, 40, 47, 35), holder='D',
                            status=BeloteStatus.Rebelote_Played), 0, 182)


@pytest.mark.parametrize('taker', list('ABCD'))
def test_classic_team_scoring_is_independent_of_taker_seat(taker):
    game = make_game(holder='D', status=BeloteStatus.Rebelote_Played)
    game.taker = game.get_player_by_name(taker)
    assert_scores(game, 0 if taker in 'AC' else 60, 182 if taker in 'AC' else 122)


@pytest.mark.parametrize('points,holder,expected_carry', [
    ((40, 40, 41, 41), None, 81),
    ((35, 45, 36, 46), 'A', 91),
    ((45, 35, 46, 36), 'D', 91),
])
def test_litige_credits_defense_and_carries_entire_team_total(points, holder, expected_carry):
    game = make_game(points=points, holder=holder,
                     status=BeloteStatus.Rebelote_Played if holder else BeloteStatus.Not_Allowed)
    game.bonus_litige = 81
    assert_scores(game, 0, expected_carry)
    assert game.bonus_litige == 81 + expected_carry
    assert game.hand_winner == ['']
    game.deal(dealer=game.players[-1])
    game.taker = game.players[0]
    game.hand_points.update(zip(game.players, (60, 30, 40, 32)))
    game.wins.update(dict.fromkeys(game.players, 2))
    assert_scores(game, 181 + expected_carry, 62 + expected_carry)
    assert game.bonus_litige == 0


@pytest.mark.parametrize('points,wins,holder,expected', [
    ((100, 0, 62, 0), (4, 0, 4, 0), 'B', (252, 20)),
    ((0, 100, 0, 62), (0, 4, 0, 4), 'A', (20, 252)),
])
def test_classic_capot_preserves_losing_teams_completed_belote(points, wins, holder, expected):
    game = make_game(points=points, wins=wins, holder=holder,
                     status=BeloteStatus.Rebelote_Played)
    assert_scores(game, *expected)


@pytest.mark.parametrize('game_type', [BeloteGame, ContreeGame])
def test_hand_completion_is_idempotent_and_next_deal_resets_it(game_type):
    game = make_game(game_type, points=(60, 30, 40, 32))
    game.hand_completed()
    scores = dict(game.scores)
    hand_points = dict(game.hand_points)
    game.hand_completed()
    assert game.scores == scores
    assert game.hand_points == hand_points
    assert len(game.scoresheet) == 1
    game.deal(dealer=game.players[-1])
    assert not game._hand_scored


@pytest.mark.parametrize('counting,expected', [
    (CountingMethod.POINTS_ACHIEVED, (0, 180)),
    (CountingMethod.POINTS_ACHIEVED_PLUS_BID, (0, 300)),
    (CountingMethod.POINTS_BID, (0, 160)),
])
@pytest.mark.parametrize('holder', list('ABCD'))
def test_contree_failed_contract_award_in_each_mode(counting, expected, holder):
    game = make_game(ContreeGame, bid=120, counting=counting,
                     holder=holder, status=BeloteStatus.Rebelote_Played)
    assert_scores(game, *expected)


@pytest.mark.parametrize('counting,expected', [
    (CountingMethod.POINTS_ACHIEVED, (100, 60)),
    (CountingMethod.POINTS_ACHIEVED_PLUS_BID, (200, 60)),
    (CountingMethod.POINTS_BID, (100, 0)),
])
def test_contree_successful_contract_in_each_mode(counting, expected):
    assert_scores(make_game(ContreeGame, points=(60, 30, 40, 32), counting=counting), *expected)


@pytest.mark.parametrize('counting,expected', [
    (CountingMethod.POINTS_ACHIEVED, (110, 80)),
    (CountingMethod.POINTS_ACHIEVED_PLUS_BID, (210, 80)),
    (CountingMethod.POINTS_BID, (100, 0)),
])
def test_contree_completed_belote_can_fulfill_contract(counting, expected):
    game = make_game(ContreeGame, points=(40, 30, 45, 47), counting=counting,
                     holder='C', status=BeloteStatus.Rebelote_Played)
    assert_scores(game, *expected)


@pytest.mark.parametrize('status', [BeloteStatus.Belote_Played, BeloteStatus.Rebelote_Announced,
                                   BeloteStatus.Lost])
def test_contree_failed_takers_started_belote_transfers_even_without_rebelote(status):
    game = make_game(ContreeGame, status=status, holder='A')
    game._belote_started = True
    assert_scores(game, 0, 180)


@pytest.mark.parametrize('status', [BeloteStatus.Allowed, BeloteStatus.Lost])
def test_contree_unannounced_pair_does_not_transfer_bonus(status):
    assert_scores(make_game(ContreeGame, status=status, holder='A'), 0, 160)


@pytest.mark.parametrize('counting,multiplier,success,expected', [
    (CountingMethod.POINTS_ACHIEVED, 2, True, (340, 0)),
    (CountingMethod.POINTS_ACHIEVED, 4, True, (660, 0)),
    (CountingMethod.POINTS_ACHIEVED, 2, False, (0, 340)),
    (CountingMethod.POINTS_ACHIEVED, 4, False, (0, 660)),
    (CountingMethod.POINTS_ACHIEVED_PLUS_BID, 2, True, (540, 0)),
    (CountingMethod.POINTS_ACHIEVED_PLUS_BID, 4, True, (1060, 0)),
    (CountingMethod.POINTS_ACHIEVED_PLUS_BID, 2, False, (0, 540)),
    (CountingMethod.POINTS_ACHIEVED_PLUS_BID, 4, False, (0, 1060)),
    (CountingMethod.POINTS_BID, 2, True, (200, 0)),
    (CountingMethod.POINTS_BID, 4, True, (400, 0)),
    (CountingMethod.POINTS_BID, 2, False, (0, 320)),
    (CountingMethod.POINTS_BID, 4, False, (0, 640)),
])
@pytest.mark.parametrize('holder', ['A', 'D'])
def test_contree_doubled_contracts_award_stake_and_undoubled_bonus(counting, multiplier, success, expected, holder):
    points = (60, 30, 40, 32) if success else (20, 60, 30, 52)
    game = make_game(ContreeGame, points=points, counting=counting,
                     holder=holder, status=BeloteStatus.Rebelote_Played)
    game.contree_status = ContreStatus.CONTREE if multiplier == 2 else ContreStatus.SURCONTREE
    assert_scores(game, *expected)


@pytest.mark.parametrize('counting,expected', [
    (CountingMethod.POINTS_ACHIEVED, (90, 80)),
    (CountingMethod.POINTS_ACHIEVED_PLUS_BID, (170, 80)),
])
def test_contree_rounds_five_up(counting, expected):
    game = make_game(ContreeGame, points=(40, 40, 45, 37), bid=80, counting=counting)
    assert_scores(game, *expected)


def test_contree_checks_contract_before_rounding():
    assert_scores(make_game(ContreeGame, points=(40, 35, 49, 38), bid=90), 0, 160)


@pytest.mark.parametrize('counting,expected', [
    (CountingMethod.POINTS_ACHIEVED, (250, 0)),
    (CountingMethod.POINTS_ACHIEVED_PLUS_BID, (330, 0)),
    (CountingMethod.POINTS_BID, (80, 0)),
])
def test_contree_unrequested_capot_replaces_regular_points(counting, expected):
    game = make_game(ContreeGame, points=(100, 0, 62, 0), wins=(4, 0, 4, 0),
                     bid=80, counting=counting)
    assert_scores(game, *expected)


@pytest.mark.parametrize('multiplier,expected', [(2, (440, 0)), (4, (760, 0))])
def test_contree_unrequested_doubled_capot_premium_is_not_multiplied(multiplier, expected):
    game = make_game(ContreeGame, points=(100, 0, 62, 0), wins=(4, 0, 4, 0), bid=80,
                     holder='B', status=BeloteStatus.Rebelote_Played)
    game.contree_status = ContreStatus.CONTREE if multiplier == 2 else ContreStatus.SURCONTREE
    assert_scores(game, *expected)


@pytest.mark.parametrize('counting,success,expected', [
    (CountingMethod.POINTS_ACHIEVED, True, (500, 0)),
    (CountingMethod.POINTS_ACHIEVED, False, (0, 500)),
    (CountingMethod.POINTS_ACHIEVED_PLUS_BID, True, (500, 0)),
    (CountingMethod.POINTS_ACHIEVED_PLUS_BID, False, (0, 500)),
    (CountingMethod.POINTS_BID, True, (250, 0)),
    (CountingMethod.POINTS_BID, False, (0, 160)),
])
def test_contree_requested_capot_requires_all_eight_tricks(counting, success, expected):
    game = make_game(ContreeGame, bid=162, counting=counting,
                     points=(100, 0, 62, 0),
                     wins=(4, 0, 4, 0) if success else (3, 1, 4, 0))
    # A lost zero-point trick still defeats capot, even with all 162 card points.
    assert_scores(game, *expected)


def test_belote_cannot_substitute_for_eighth_capot_trick():
    game = make_game(ContreeGame, points=(80, 20, 62, 0), wins=(3, 1, 4, 0), bid=162,
                     holder='A', status=BeloteStatus.Rebelote_Played)
    assert_scores(game, 0, 520)


def test_numeric_160_is_distinct_from_capot():
    game = make_game(ContreeGame, points=(80, 20, 62, 0), wins=(3, 1, 4, 0), bid=160,
                     holder='A', status=BeloteStatus.Rebelote_Played)
    assert 160 in game.all_bet_points
    assert_scores(game, 160, 20)


@pytest.mark.parametrize('success,expected', [(True, (1020, 0)), (False, (0, 1020))])
def test_requested_doubled_capot_awards_fixed_stake(success, expected):
    game = make_game(ContreeGame, points=(100, 0, 62, 0), bid=162,
                     wins=(4, 0, 4, 0) if success else (3, 1, 4, 0),
                     holder='D', status=BeloteStatus.Rebelote_Played)
    game.contree_status = ContreStatus.CONTREE
    assert_scores(game, *expected)


@pytest.mark.parametrize('last_action', ['pass', 'surcontre'])
def test_taker_passing_or_surcontrant_does_not_erase_contract(last_action):
    game = make_game(ContreeGame, counting=CountingMethod.POINTS_BID)
    game.phase = game.GamePhase.BET
    game.place_bet('B', Announce('contre', 0))
    game.place_bet('C', Announce('pass', 0))
    game.place_bet('D', Announce('pass', 0))
    game.place_bet('A', Announce(last_action, 0))
    assert game.phase == game.GamePhase.PLAY
    assert game.current_bet.points == 100
    assert game.bets['A'].points == 0
    assert_scores(game, 0, 320 if last_action == 'pass' else 640)


@pytest.mark.parametrize('game_type,state_type', [(BeloteGame, BeloteState), (ContreeGame, ContreeState)])
def test_json_snapshot_restores_scoring_state(game_type, state_type):
    game = make_game(game_type, points=(60, 30, 40, 32), counting=CountingMethod.POINTS_ACHIEVED_PLUS_BID,
                     holder='C', status=BeloteStatus.Rebelote_Played)
    game._belote_started = True
    game.bonus_litige = 81
    game.win_game_points = 1500
    state = state_type(**json.loads(game.get_state().to_json()))
    restored = game_type(Player('A'))
    restored.populate_from_state(state)
    assert restored.player_with_belote == 'C'
    assert restored.belote_status is BeloteStatus.Rebelote_Played
    assert restored.wins == game.wins
    assert restored.bonus_litige == 81
    assert restored.win_game_points == 1500
    assert restored._belote_started
    if game_type is ContreeGame:
        assert restored.counting == CountingMethod.POINTS_ACHIEVED_PLUS_BID
    assert restored.update_scores() == game.update_scores()
    assert restored.hand_points == game.hand_points
    completed = state_type(**json.loads(restored.get_state().to_json()))
    restored.populate_from_state(completed)
    scores = dict(restored.scores)
    assert restored.update_scores() == scores


def test_older_snapshot_reconstructs_completed_trick_counts():
    game = make_game()
    set_hands(game, {'A': ['s11', 'h7'], 'B': ['s7', 'h8'],
                     'C': ['s8', 'h9'], 'D': ['s9', 'h10']})
    game.create_round()
    for player in game.players:
        game.play_card(player, game.hands[player].serialize()[0])
    state_data = json.loads(game.get_state().to_json())
    state_data.pop('nb_rounds_won')
    restored = BeloteGame(Player('A'))
    restored.populate_from_state(BeloteState(**state_data))
    assert restored.wins['A'] == 1
    assert sum(restored.wins.values()) == 1


@pytest.mark.parametrize('game_type', [BeloteGame, ContreeGame])
@pytest.mark.parametrize('scores,over', [((1000, 999), True), ((999, 999), False),
                                       ((1100, 1100), False), ((1100, 1110), True)])
def test_game_end_requires_target_and_unique_winning_team(game_type, scores, over):
    game = make_game(game_type)
    game.scores.update(zip(game.players, scores * 2))
    assert game.is_game_over() is over


def set_hands(game, hands):
    for player, values in hands.items():
        hand = Hand(None)
        for value in values:
            hand.add(Card.card_from_value(value))
        game.hands[player] = hand
    game.set_cards_rank_and_value()


@pytest.mark.parametrize('game_type,expected', [(BeloteGame, (0, 162)), (ContreeGame, (0, 180))])
def test_missing_rebelote_after_playing_announced_first_card(game_type, expected):
    game = make_game(game_type, holder='A', status=BeloteStatus.Allowed)
    set_hands(game, {'A': ['s12', 's13'], 'B': ['c7', 'c8'],
                     'C': ['d7', 'd8'], 'D': ['h7', 'h8']})
    game.create_round()
    game.player_announced_belote('B', game.BeloteAnnounced.BELOTE)
    assert game.belote_status == BeloteStatus.Allowed
    game.player_announced_belote('A', game.BeloteAnnounced.BELOTE)
    for player in game.players:
        game.play_card(player, game.hands[player].serialize()[0])
    assert game.belote_status == BeloteStatus.Belote_Played
    game.create_round()
    game.play_card('A', 's13')
    assert game.belote_status == BeloteStatus.Lost
    assert game._belote_started
    game.hand_points.update(zip(game.players, (30, 50, 30, 52)))
    game.wins.update(dict.fromkeys(game.players, 2))
    assert_scores(game, *expected)


@pytest.mark.parametrize('completed,expected', [(False, (0, 162)), (True, (20, 162))])
def test_two_player_failed_contract_does_not_duplicate_belote(completed, expected):
    game = BeloteGame(Player('A'))
    game.add_player(Player('A'))
    game.add_player(Player('B'))
    game.taker = game.players[0]
    game.hand_points.update({'A': 60, 'B': 102})
    game.wins.update({'A': 4, 'B': 5})
    game.player_with_belote = game.players[0]
    game.belote_status = BeloteStatus.Rebelote_Played if completed else BeloteStatus.Lost
    game.update_scores()
    assert (game.scores['A'], game.scores['B']) == expected


@pytest.mark.parametrize('points,expected', [((80, 50, 32), (80, 50, 32)),
                                            ((40, 70, 52), (0, 110, 52)),
                                            ((40, 61, 61), (0, 81, 81))])
def test_three_player_variant_keeps_individual_scoring(points, expected):
    game = BeloteGame(Player('A'))
    for name in 'ABC':
        game.add_player(Player(name))
    game.taker = game.players[0]
    game.hand_points.update(zip(game.players, points))
    game.wins.update(dict.fromkeys(game.players, 3))
    game.update_scores()
    assert tuple(game.scores[player] for player in game.players) == expected


def test_single_player_practice_hand_keeps_existing_zero_score():
    game = BeloteGame(Player('A'))
    game.add_player(Player('A'))
    game.taker = game.players[0]
    game.hand_points['A'] = 100
    game.wins['A'] = 9
    assert game.update_scores()['A'] == 0


@pytest.mark.parametrize('game_type,expected', [(BeloteGame, ['s7']), (ContreeGame, ['s7', 'd14'])])
def test_undertrumping_differs_between_classic_and_contree(game_type, expected):
    game = make_game(game_type)
    set_hands(game, {'A': ['s7', 'd14'], 'B': ['h7'], 'C': ['h14'], 'D': ['s11']})
    game.create_round()
    game.play_card('C', 'h14')
    game.play_card('D', 's11')
    assert game.get_allowed_cards('A') == expected


@pytest.mark.parametrize('hands,expected', [
    ({'A': ['s9', 's7', 'd14'], 'C': ['h14'], 'D': ['s10']}, ['s9']),
    ({'A': ['s7', 'd14'], 'C': ['s11'], 'D': ['h14']}, ['s7']),
    ({'A': ['s7', 'd14'], 'C': ['h14'], 'D': ['h7']}, ['s7', 'd14']),
])
def test_contree_still_requires_following_suit_and_overtrumping(hands, expected):
    game = make_game(ContreeGame)
    set_hands(game, hands)
    game.create_round()
    game.play_card('C', hands['C'][0])
    game.play_card('D', hands['D'][0])
    assert game.get_allowed_cards('A') == expected


@pytest.mark.parametrize('sim_type,game_type', [(BeloteSim, BeloteGame), (ContreeSim, ContreeGame)])
def test_simulations_complete_belote_declarations(sim_type, game_type):
    game = make_game(game_type, holder='A', status=BeloteStatus.Allowed)
    set_hands(game, {'A': ['s12', 's13'], 'B': ['c7', 'c8'],
                     'C': ['d7', 'd8'], 'D': ['h7', 'h8']})
    game.active_player = game.players[0]
    game.create_round()

    class FirstLegalCard:
        def get_action(self, state):
            return state.allowed_cards[0]

    sim = sim_type(FirstLegalCard(), FirstLegalCard(), 'A', game.get_state())
    for _ in range(4):
        sim.play_single_move()
    assert sim.belote_status == BeloteStatus.Belote_Played
    sim.create_round()
    sim.active_player = sim.players[0]
    sim.play_single_move()
    assert sim.belote_status == BeloteStatus.Rebelote_Played
