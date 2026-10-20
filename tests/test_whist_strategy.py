"""Exact-bid evaluation, public information and tactical Whist regressions."""

import copy
import json
import random
from types import SimpleNamespace

import pytest

from romwhist.card import Card
from romwhist.game import CardGame
from romwhist.hand import Hand
from romwhist.ohell.ohell import OhellGame
from romwhist.ohell.ohell_ai import OhellAiPlayer
from romwhist.ohell.ohell_search import WhistSearchAgent
from romwhist.ohell.ohell_sim import OhellSim
from romwhist.ohell.ohell_state import OhellState
from romwhist.ohell.ohell_strategy import WhistTacticalAgent, inferred_voids, sample_hidden_hands
from romwhist.player import Player


def make_game(hands=None, bids=None, trump=None, deck_size=32, bonus=1):
    hands = hands or {'A': ['h7', 'h14'], 'B': ['h10', 'c7'],
                      'C': ['h9', 'd7'], 'D': ['h8', 's7']}
    game = OhellGame('A', bonus_win=bonus)
    for name in hands:
        game.add_player(Player(name))
    game.dealing_method = CardGame.MANUAL_DEALING
    game.start_game()
    game.deck_size = deck_size
    game.deal(nb_cards=len(next(iter(hands.values()))), dealer=game.players[-1])
    for player, values in hands.items():
        game.hands[player] = Hand(None)
        game.hands[player].cards = [Card.card_from_value(value) for value in values]
    game.bets.update(bids or dict.fromkeys(game.players, 0))
    game.phase = game.GamePhase.PLAY
    game.trump_suit = trump
    game.trump_card = None
    game.create_round()
    return game


@pytest.mark.parametrize('bid,expected', [(0, 'h7'), (1, 'h14')])
def test_policy_wins_or_loses_according_to_target(bid, expected):
    game = make_game(bids={'A': bid, 'B': 0, 'C': 0, 'D': 0})
    for player, card in [('B', 'h10'), ('C', 'h9'), ('D', 'h8')]:
        game.play_card(player, card)
    assert WhistTacticalAgent().choose_card(game) == expected


def test_reached_target_dumps_highest_losing_card():
    game = make_game(hands={'A': ['h7', 'h13'], 'B': ['h14', 'c7'],
                            'C': ['h9', 'd7'], 'D': ['h8', 's7']})
    game.bets['A'] = game.wins['A'] = 2
    for player, card in [('B', 'h14'), ('C', 'h9'), ('D', 'h8')]:
        game.play_card(player, card)
    assert WhistTacticalAgent().choose_card(game) == 'h13'


def test_avoiding_tricks_does_not_cut_unnecessarily():
    game = make_game(hands={'A': ['c14', 's14'], 'B': ['h14', 'c7'],
                            'C': ['h9', 'd7'], 'D': ['h8', 's7']}, trump='club')
    for player, card in [('B', 'h14'), ('C', 'h9'), ('D', 'h8')]:
        game.play_card(player, card)
    assert WhistTacticalAgent().choose_card(game) == 's14'


def exact_target_position(bid=0, bonus=1):
    # Every heart is accounted for, so remaining opponents cannot hold one.
    game = make_game(hands={'A': ['h10', 'h14'], 'B': ['h11', 'c10'],
                            'C': ['h12', 'd10'], 'D': ['h13', 's10']},
                     bids={'A': bid, 'B': 0, 'C': 0, 'D': 0}, deck_size=20, bonus=bonus)
    for player, card in [('B', 'h11'), ('C', 'h12'), ('D', 'h13')]:
        game.play_card(player, card)
    return game


@pytest.mark.parametrize('bid,expected', [(0, 'h10'), (2, 'h14')])
def test_search_changes_card_for_zero_and_two_trick_targets(bid, expected):
    game = exact_target_position(bid)
    agent = WhistSearchAgent('OhellSim', 'A')
    agent.num_simulations = agent.min_num_simulations = 4
    try:
        assert agent.get_action(game.get_state()) == expected
    finally:
        agent.executor.shutdown()


@pytest.mark.parametrize('bid,card,expected', [(0, 'h10', 7), (0, 'h14', -2),
                                            (2, 'h14', 9), (2, 'h10', -2)])
def test_full_rollout_evaluates_exact_bid_score_and_custom_bonus(bid, card, expected):
    game = exact_target_position(bid, bonus=7)
    state = game.get_state()
    original = json.loads(state.to_json())
    sim = OhellSim(WhistTacticalAgent(), WhistTacticalAgent(), 'A', state,
                   starting_action=card, one_round_only=True, seed=3)
    sim.run()
    assert sim.evaluation_score == expected
    assert sim.evaluation_score == sim.hand_points['A']
    assert sim.sim_player_won() is (expected > 0)
    assert json.loads(state.to_json()) == original


def test_rollout_preserves_already_won_tricks():
    game = exact_target_position(4, bonus=7)
    game.wins['A'] = 2
    sim = OhellSim(WhistTacticalAgent(), WhistTacticalAgent(), 'A', game.get_state(),
                   starting_action='h14', seed=5)
    sim.run()
    assert sim.wins['A'] == 4
    assert sim.evaluation_score == 11


def test_snapshot_keeps_bonus_leader_and_independent_trick_counts():
    game = make_game(bonus=9)
    game.play_card('C', 'h9')
    game.play_card('D', 'h8')
    game.play_card('A', 'h7')
    game.wins['A'] = 2
    state = game.get_state()
    restored = OhellGame('A')
    restored.populate_from_state(OhellState(**json.loads(state.to_json())))
    assert restored.bonus_win == 9
    assert restored.current_round.first_player == 'C'
    assert str(restored.current_round.get_first_card_played()) == 'h9'
    assert restored.get_allowed_cards('B') == ['h10']
    state.nb_rounds_won['A'] = 10
    assert game.wins['A'] == restored.wins['A'] == 2


def test_old_snapshot_reconstructs_leader_from_previous_winner():
    game = make_game()
    for player, card in [('A', 'h7'), ('B', 'h10'), ('C', 'h9'), ('D', 'h8')]:
        game.play_card(player, card)
    game.create_round()
    game.play_card('B', 'c7')
    game.play_card('C', 'd7')
    game.play_card('D', 's7')
    data = json.loads(game.get_state().to_json())
    data.pop('round_leaders')
    restored = OhellGame('A')
    restored.populate_from_state(OhellState(**data))
    assert restored.current_round.first_player == 'B'
    assert str(restored.current_round.get_first_card_played()) == 'c7'


def test_discard_proves_only_asked_suit_void():
    game = make_game(hands={'A': ['c7', 's14'], 'B': ['h14', 'c8'],
                            'C': ['h9', 'd7'], 'D': ['h8', 's7']}, trump='club')
    game.play_card('B', 'h14')
    game.play_card('C', 'h9')
    game.play_card('D', 'h8')
    game.play_card('A', 's14')
    assert inferred_voids(game)['A'] == {'heart'}


def test_sampling_ignores_private_hands_and_excludes_face_up_trump():
    game = make_game()
    game.trump_card = Card.card_from_value('c14')
    observations = [game.get_state(), copy.deepcopy(game.get_state())]
    for player in ['B', 'C', 'D']:
        observations[1].hand_cards[player] = ['c7'] * len(observations[1].hand_cards[player])
    assignments = []
    for state in observations:
        sim = OhellSim(WhistTacticalAgent(), WhistTacticalAgent(), 'A', state, seed=18)
        sample_hidden_hands(sim, 'A', sim.rng)
        assignments.append({str(player): hand.serialize() for player, hand in sim.hands.items()})
    assert assignments[0] == assignments[1]
    assert all('c14' not in hand for hand in assignments[0].values())


@pytest.mark.parametrize('players,deck,cards,trump', [(2, 32, 4, True), (3, 32, 4, False),
                                                    (4, 52, 5, True), (6, 48, 4, False)])
def test_public_constraints_hold_through_complete_hands(players, deck, cards, trump):
    random.seed(players)
    game = OhellGame('p0')
    for index in range(players):
        game.add_player(Player(f'p{index}'))
    game.dealing_method = CardGame.MANUAL_DEALING
    game.start_game()
    game.deck_size = deck
    game.deal(nb_cards=cards, with_trump=trump, dealer=game.players[-1])
    for player in game.players:
        game.bets[player] = 1
    game.phase = game.GamePhase.PLAY
    game.create_round()
    while not game.is_hand_completed():
        observer = game.active_player
        sim = OhellSim(WhistTacticalAgent(), WhistTacticalAgent(), observer, game.get_state(), seed=1)
        sample_hidden_hands(sim, observer, sim.rng)
        voids = inferred_voids(game)
        for player in game.players:
            assert len(sim.hands[player].cards) == len(game.hands[player].cards)
            if player != observer:
                assert not any(card.get_suit_name() in voids[player] for card in sim.hands[player].cards)
        winner = game.play_card(observer, WhistTacticalAgent().choose_card(game))
        if winner is not None and not game.is_hand_completed():
            game.create_round()


def test_unannounced_bids_are_modelled_without_overwriting_known_bids():
    game = make_game(bids={'A': 1, 'B': 0, 'C': -1, 'D': -1})
    game.phase = game.GamePhase.BET
    sim = OhellSim(WhistTacticalAgent(), WhistTacticalAgent(), 'A', game.get_state(), seed=1)
    sample_hidden_hands(sim, 'A', sim.rng)
    sim._complete_bids()
    assert sim.bets['A'] == 1
    assert sim.bets['B'] == 0
    assert all(0 <= bid <= 2 for bid in sim.bets.values())
    assert sum(sim.bets.values()) != 2
    assert game.bets['C'] == -1


def test_search_compares_unfavorable_options_without_win_cutoff():
    agent = WhistSearchAgent('OhellSim', 'A')
    try:
        agent.action_points = {'h7': -100, 'h14': -20}
        agent.action_value = {'h7': 0, 'h14': 0}
        agent.num_simulations_per_action = {'h7': 20, 'h14': 20}
        assert agent._best(['h7', 'h14']) == 'h14'
    finally:
        agent.executor.shutdown()


def test_candidate_cards_share_same_sample_seed(monkeypatch):
    calls = []

    class FakeSim:
        def __init__(self, *args, **kwargs):
            calls.append((args[4], kwargs['seed']))
            self.evaluation_score = -1

        def run(self):
            return True

        def sim_player_won(self):
            return False

    monkeypatch.setattr('romwhist.ohell.ohell_search.OhellSim', FakeSim)
    agent = WhistSearchAgent('OhellSim', 'A')
    agent.num_simulations = agent.min_num_simulations = 2
    try:
        assert agent._run(SimpleNamespace(), ['h7', 'h14']) in ['h7', 'h14']
        assert len(calls) == 4
        assert calls[0][1] == calls[1][1]
        assert calls[2][1] == calls[3][1]
    finally:
        agent.executor.shutdown()


def test_ai_respects_forbidden_last_bid():
    game = make_game(bids={'A': 1, 'B': 0, 'C': 0, 'D': -1})
    game.phase = game.GamePhase.BET
    game.active_player = game.players[-1]
    allowed = game.get_allowed_bets(game.active_player)
    assert 1 not in allowed
    ai = OhellAiPlayer(game.active_player, 'test')
    ai._OhellAiPlayer__agent2.num_simulations = 3
    ai._OhellAiPlayer__agent2.min_num_simulations = 3
    try:
        assert ai.player_to_bet(allowed, game.get_state().to_json()) in allowed
    finally:
        ai._OhellAiPlayer__agent.executor.shutdown()
        ai._OhellAiPlayer__agent2.executor.shutdown()
