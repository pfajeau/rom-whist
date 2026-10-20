"""Tactical, inference, evaluation and bidding regressions for the card AI."""

import copy
import json
import random
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from romwhist import app
from romwhist.belote.belote import BeloteGame
from romwhist.belote.belote_ai import BeloteAiPlayer
from romwhist.belote.belote_inference import inferred_voids, sample_hidden_hands
from romwhist.belote.belote_search import BeloteSearchAgent
from romwhist.belote.belote_sim import BeloteSim
from romwhist.belote.belote_state import BeloteState
from romwhist.belote.belote_status import BeloteStatus
from romwhist.belote.belote_tactics import TacticalAgent
from romwhist.card import Card
from romwhist.contree.contree import ContreeGame
from romwhist.contree.announce import Announce, ContreStatus
from romwhist.contree.contree_ai import ContreeAiPlayer
from romwhist.contree.contree_state import ContreeState
from romwhist.contree.contree_sim import ContreeSim
from romwhist.deck import Deck
from romwhist.hand import Hand
from romwhist.player import Player
from tests.test_belote_scoring import make_game, set_hands


@pytest.fixture(autouse=True)
def context():
    with app.app_context():
        yield


def test_lost_rollout_has_zero_points_despite_previously_earned_points():
    game = make_game(points=(30, 40, 10, 20))
    set_hands(game, {'A': ['h7'], 'B': [], 'C': [], 'D': []})
    game.trump_card = None
    game.create_round()
    for player, card in [('B', 'h14'), ('C', 'h8'), ('D', 'h9')]:
        game.current_round.card_played(player, Card.card_from_value(card))
    game.active_player = game.players[0]
    game.set_cards_rank_and_value()
    sim = BeloteSim(TacticalAgent(), TacticalAgent(), 'A', game.get_state(),
                    starting_action='h7', one_round_only=True, seed=1)
    sim.run()
    assert sim.hand_points['A'] == sim.hand_points['C'] == 0
    assert not sim.sim_player_won()
    assert sim.evaluation_score < 0


def test_snapshot_preserves_actual_leader_when_player_order_differs():
    game = make_game()
    set_hands(game, {'A': ['h8', 's7'], 'B': ['h9', 's8'],
                     'C': ['h14', 's9'], 'D': ['h7', 's10']})
    game.create_round()
    for player in ['C', 'D', 'A']:
        game.play_card(player, game.hands[player].serialize()[0])
    restored = BeloteGame('A')
    restored.populate_from_state(BeloteState(**json.loads(game.get_state().to_json())))
    assert restored.current_round.first_player == 'C'
    assert str(restored.current_round.get_first_card_played()) == 'h14'
    assert restored.get_allowed_cards('B') == ['h9']


@pytest.mark.parametrize('own,plays,expected', [
    (['h10', 'h14'], [('B', 'h13'), ('C', 'h7'), ('D', 'h8')], 'h10'),
    (['s7', 'd10'], [('B', 'h13'), ('C', 'h14'), ('D', 'h8')], 'd10'),
    (['s7', 'd10'], [('C', 'h14'), ('D', 'h8')], 's7'),
    (['s7', 'h10'], [('B', 'c11'), ('C', 'c9'), ('D', 'c7')], 's7'),
])
def test_tactical_policy_wins_cheaply_and_supports_partner(own, plays, expected):
    game = make_game()
    game.trump_suit = 'club'
    set_hands(game, {'A': own})
    game.create_round()
    for player, value in plays:
        game.current_round.card_played(player, Card.card_from_value(value))
    game.active_player = game.players[0]
    game.set_cards_rank_and_value()
    assert TacticalAgent().choose_card(game) == expected


@pytest.mark.parametrize('game_type,expected_trump_void', [(BeloteGame, True), (ContreeGame, False)])
def test_void_inference_respects_contree_discard_exception(game_type, expected_trump_void):
    game = make_game(game_type)
    game.trump_suit = 'club'
    game.create_round()
    for player, value in [('C', 'h14'), ('D', 'c11'), ('A', 'd7')]:
        game.current_round.card_played(player, Card.card_from_value(value))
    game.set_cards_rank_and_value()
    voids = inferred_voids(game)
    assert 'heart' in voids['A']
    assert ('club' in voids['A']) is expected_trump_void


def test_partner_winning_does_not_imply_trump_void_on_discard():
    game = make_game()
    game.create_round()
    for player, value in [('C', 'h14'), ('D', 'h8'), ('A', 'd7')]:
        game.current_round.card_played(player, Card.card_from_value(value))
    assert inferred_voids(game)['A'] == {'heart'}


def test_sampler_preserves_public_belote_remaining_card():
    game = make_game()
    game.trump_suit = 'club'
    game.trump_card = None
    cards = Deck(32).cards
    ordered = ['c12', 'c13'] + [str(card) for card in cards if str(card) not in ('c12', 'c13')]
    set_hands(game, dict(zip(['D', 'A', 'B', 'C'], [ordered[index:index + 8] for index in range(0, 32, 8)])))
    game.create_round()
    game.belote_status = BeloteStatus.Allowed
    game.player_with_belote = game.get_player_by_name('D')
    game.player_announced_belote('D', game.BeloteAnnounced.BELOTE)
    game.play_card('D', 'c12')
    for seed in range(10):
        sim = BeloteSim(TacticalAgent(), TacticalAgent(), 'A', game.get_state(), seed=seed)
        sample_hidden_hands(sim, 'A', sim.rng)
        assert 'c13' in sim.hands['D'].serialize()
        assert all('c12' not in hand.serialize() for hand in sim.hands.values())


def test_sampler_does_not_use_actual_opponents_hands_or_unannounced_owner():
    game = make_game()
    game.trump_card = None
    state = game.get_state()
    changed = copy.deepcopy(state)
    for player in ['B', 'C', 'D']:
        changed.hand_cards[player] = ['c7'] * len(changed.hand_cards[player])
    state.player_with_belote = 'B'
    changed.player_with_belote = 'D'
    state.belote_status = changed.belote_status = BeloteStatus.Allowed
    deals = []
    for observation in [state, changed]:
        sim = BeloteSim(TacticalAgent(), TacticalAgent(), 'A', observation, seed=22)
        sample_hidden_hands(sim, 'A', sim.rng)
        deals.append({str(player): hand.serialize() for player, hand in sim.hands.items()})
    assert deals[0] == deals[1]


@pytest.mark.parametrize('seed', range(5))
def test_sampled_deals_respect_public_history_throughout_real_hand(seed):
    random.seed(seed)
    game = BeloteGame('A')
    for name in 'ABCD':
        game.add_player(Player(name))
    game.start_game()
    game.deal(dealer=game.players[-1])
    game.place_bet(game.players[0], 'club')
    game.deal_2()
    game.create_round()
    while not game.is_hand_completed():
        observer = game.active_player
        sim = BeloteSim(TacticalAgent(), TacticalAgent(), observer, game.get_state(), seed=seed)
        sample_hidden_hands(sim, observer, sim.rng)
        voids = inferred_voids(game)
        for player in game.players:
            if player != observer:
                assert len(sim.hands[player].cards) == len(game.hands[player].cards)
                assert not any(card.get_suit_name() in voids[player] for card in sim.hands[player].cards)
        known = [str(card) for hand in sim.hands.values() for card in hand.cards]
        assert len(known) == len(set(known))
        winner = game.play_card(observer, TacticalAgent().choose_card(game))
        if winner is not None and not game.is_hand_completed():
            game.create_round()


def test_card_selection_keeps_best_negative_value_below_win_cutoff():
    agent = BeloteSearchAgent('BeloteSim', 'A')
    try:
        agent.num_simulations_per_action = {'h7': 20, 'h14': 20}
        agent.action_value = {'h7': 0, 'h14': 4}
        agent.action_points = {'h7': -300, 'h14': -100}
        assert agent._best(['h7', 'h14']) == 'h14'
        assert agent._best(['h7', 'h14'], bidding=True) is None
    finally:
        agent.executor.shutdown()


def test_classic_bidding_filters_pass_without_mutating_observation():
    agent = BeloteSearchAgent('BeloteSim', 'A')
    state = BeloteState('test', allowed_bets=['pass', 'club', 'heart'])
    agent._run = MagicMock(return_value='club')
    try:
        assert agent.get_bet(state) == 'club'
        agent._run.assert_called_once_with(state, ['club', 'heart'], bidding=True)
        assert state.allowed_bets == ['pass', 'club', 'heart']
    finally:
        agent.executor.shutdown()


@pytest.mark.parametrize('cards,one_round', [(4, True), (3, False)])
def test_search_uses_paired_samples_and_full_hand_endgames(monkeypatch, cards, one_round):
    calls = []

    class FakeSim:
        def __init__(self, *args, **kwargs):
            calls.append((args[4], kwargs['seed'], kwargs['one_round_only']))
            self.evaluation_score = -10

        def run(self):
            return True

        def sim_player_won(self):
            return False

    monkeypatch.setattr('romwhist.belote.belote_search.BeloteSim', FakeSim)
    state = SimpleNamespace(hand_cards={'A': ['x'] * cards})
    agent = BeloteSearchAgent('BeloteSim', 'A')
    agent.num_simulations = agent.min_num_simulations = 2
    try:
        assert agent._run(state, ['h7', 'h14'], bidding=False) in ['h7', 'h14']
        assert len(calls) == 4
        assert calls[0][1] == calls[1][1]
        assert calls[2][1] == calls[3][1]
        assert all(call[2] is one_round for call in calls)
    finally:
        agent.executor.shutdown()


def test_contree_enumerates_only_real_legal_contracts():
    state = ContreeState('test', allowed_bets=[['pass', 'club', 'heart', 'contre'], [100, 110, 162]])
    assert state.get_legal_bets() == ['pass_0', 'club_100', 'club_110', 'club_162',
                                      'heart_100', 'heart_110', 'heart_162', 'contre_0']
    state.allowed_bets = [['pass', 'surcontre'], []]
    assert state.get_legal_bets() == ['pass_0', 'surcontre_0']


@pytest.mark.parametrize('action', ['club_110', 'contre_0', 'surcontre_0', 'pass_0'])
def test_contree_returns_exact_evaluated_bid(action):
    ai = ContreeAiPlayer(Player('A'), 'test')
    try:
        ai._agent2.get_bet = MagicMock(return_value=action)
        allowed = [['pass', 'club', 'contre', 'surcontre'], [100, 110]]
        state = ContreeState('test', allowed_bets=allowed)
        bet = ai.player_to_bet(allowed, state.to_json())
        assert str(bet) == action
    finally:
        ai._agent.executor.shutdown()
        ai._agent2.executor.shutdown()


@pytest.mark.parametrize('allowed,taker,status,expected', [
    ([['pass', 'contre'], []], 'B', ContreStatus.NORMAL, 'contre_0'),
    ([['pass', 'surcontre'], []], 'A', ContreStatus.CONTREE, 'surcontre_0'),
    ([['pass', 'club'], [110, 120, 162]], 'B', ContreStatus.NORMAL, 'club_162'),
])
def test_contree_search_can_raise_counter_and_surcounter(allowed, taker, status, expected):
    game = make_game(ContreeGame)
    game.phase = game.GamePhase.BET
    game.trump_suit = 'club'
    game.trump_card = None
    game.taker = game.get_player_by_name(taker)
    game.current_bet = Announce('club', 100)
    game.bets[game.taker] = game.current_bet
    game.contree_status = status
    game.active_player = game.players[0]
    game.hand_points = dict.fromkeys(game.players, 0)
    game.wins = dict.fromkeys(game.players, 0)
    set_hands(game, {player: [suit + str(rank) for rank in range(7, 15)]
                     for player, suit in zip(game.players, 'cdhs')})
    state = game.get_state()
    state.allowed_bets = allowed
    agent = BeloteSearchAgent('ContreeSim', 'A')
    agent.num_simulations = agent.min_num_simulations = 3
    try:
        assert agent.get_bet(state) == expected
        assert set(agent.num_simulations_per_action) == set(state.get_legal_bets())
    finally:
        agent.executor.shutdown()


def test_reusing_rollout_for_another_contract_preserves_original_result():
    game = make_game(ContreeGame, bid=110)
    game.phase = game.GamePhase.BET
    game.active_player = game.players[0]
    game.hand_points = dict.fromkeys(game.players, 0)
    game.wins = dict.fromkeys(game.players, 0)
    game.trump_suit = 'club'
    game.current_bet = Announce('club', 110)
    game.bets['A'] = game.current_bet
    set_hands(game, {player: [suit + str(rank) for rank in range(7, 15)]
                     for player, suit in zip(game.players, 'cdhs')})
    sim = ContreeSim(TacticalAgent(), TacticalAgent(), 'A', game.get_state(), seed=7)
    sim.run()
    scores = sim.scores.copy()
    hand_points = sim.hand_points.copy()
    assert sim.evaluate_contract('club_162') == (520, True)
    assert sim.evaluate_contract('club_110') == (270, True)
    assert sim.scores == scores
    assert sim.hand_points == hand_points
    assert sim.current_bet.points == 110
