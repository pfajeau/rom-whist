"""An AI service must recover the server's pending turn after a lost move."""

import json
from unittest.mock import MagicMock

import pytest

from romwhist import app, socketio
from romwhist.ai import ai
from romwhist.belote import belote_routes
from romwhist.belote.belote import BeloteGame
from romwhist.belote.belote_state import BeloteState
from romwhist.card import Card
from romwhist.contree import contree_routes
from romwhist.contree.announce import Announce
from romwhist.contree.contree import ContreeGame
from romwhist.hand import Hand
from romwhist.ohell import ohell_routes
from romwhist.ohell.ohell import OhellGame
from romwhist.player import Player


@pytest.fixture
def game():
    game = BeloteGame(Player('human'), id='reconnect')
    for name in ['human', 'ai1', 'ai2', 'ai3']:
        player = Player(name)
        if name != 'human':
            player.player_type = Player.PlayerType.AI
        game.add_player(player)
    game.start_game()
    game.deal(dealer=game.players[-1])
    game.place_bet(game.players[0], 'club')
    game.deal_2()
    # Replay the stuck turn: ai1 led a heart; ai2 must follow with h14.
    for player, values in zip(game.players, [['c14', 'h13'], ['h7', 's14'],
                                            ['h14', 'c13'], ['h8', 's8']]):
        hand = Hand(None)
        for value in values:
            hand.add(Card.card_from_value(value))
        game.hands[player] = hand
    game.set_cards_rank_and_value()
    game.create_round()
    game.active_player = game.players[1]
    game.play_card(game.active_player, 'h7')
    return game


def resume(client, players=None):
    return client.emit('resume ai games', {'players': players or {
        'reconnect': ['ai1', 'ai2', 'ai3']}}, namespace='/belote_ai', callback=True)


def test_lost_move_is_reissued_after_reconnect_and_advances_turn(game, monkeypatch):
    monkeypatch.setitem(belote_routes.games, 'reconnect', game)
    old_client = socketio.test_client(app, namespace='/belote_ai')
    old_client.disconnect(namespace='/belote_ai')
    client = socketio.test_client(app, namespace='/belote_ai')
    try:
        assert resume(client) == {'ok': True, 'resumed': 1}
        [event] = client.get_received('/belote_ai')
        assert event['name'] == 'player to play'
        data = event['args'][0]
        assert data['player'] == 'ai2'
        assert data['allowed_cards'] == ['h14']
        state = BeloteState(**json.loads(data['state']))
        assert state.active_player == 'ai2'
        assert state.players_type['ai2'] == 'AI'
        ack = client.emit('player played', {'game_id': 'reconnect', 'player': 'ai2', 'card': 'h14'},
                          namespace='/belote_ai', callback=True)
        assert ack == {'ok': True}
        assert game.active_player == 'ai3'
        assert 'h14' not in game.hands['ai2'].serialize()
    finally:
        client.disconnect(namespace='/belote_ai')


def test_reconnect_does_not_repeat_a_move_already_received(game, monkeypatch):
    monkeypatch.setitem(belote_routes.games, 'reconnect', game)
    game.play_card(game.active_player, 'h14')
    client = socketio.test_client(app, namespace='/belote_ai')
    try:
        assert resume(client) == {'ok': True, 'resumed': 1}
        [event] = client.get_received('/belote_ai')
        assert event['args'][0]['player'] == 'ai3'
    finally:
        client.disconnect(namespace='/belote_ai')


@pytest.mark.parametrize('phase', ['Bet', 'Bet2'])
def test_reconnect_recovers_betting_turn(game, monkeypatch, phase):
    monkeypatch.setitem(belote_routes.games, 'reconnect', game)
    game.phase = game.GamePhase(phase)
    client = socketio.test_client(app, namespace='/belote_ai')
    try:
        assert resume(client) == {'ok': True, 'resumed': 1}
        [event] = client.get_received('/belote_ai')
        assert event['name'] == 'player to bet'
        assert event['args'][0]['allowed_bets'] == game.get_allowed_bets(game.active_player)
    finally:
        client.disconnect(namespace='/belote_ai')


@pytest.mark.parametrize('case', ['unknown_game', 'human_turn', 'other_service', 'completed_trick', 'deal'])
def test_reconnect_skips_turns_that_should_not_be_replayed(game, monkeypatch, case):
    monkeypatch.setitem(belote_routes.games, 'reconnect', game)
    players = {'reconnect': ['ai1', 'ai2', 'ai3']}
    if case == 'unknown_game':
        players = {'missing': ['ai1']}
    elif case == 'human_turn':
        game.active_player = game.players[0]
        players['reconnect'].append('human')
    elif case == 'other_service':
        players = {'reconnect': ['ai1']}
    elif case == 'completed_trick':
        game.play_card('ai2', 'h14')
        game.play_card('ai3', 'h8')
        game.play_card('human', 'h13')
    elif case == 'deal':
        game.phase = game.GamePhase.DEAL
    client = socketio.test_client(app, namespace='/belote_ai')
    try:
        assert resume(client, players) == {'ok': True, 'resumed': 0}
        assert client.get_received('/belote_ai') == []
    finally:
        client.disconnect(namespace='/belote_ai')


@pytest.mark.parametrize('routes,game_type', [(contree_routes, ContreeGame), (ohell_routes, OhellGame)])
def test_other_card_game_services_can_recover_turns(routes, game_type, monkeypatch):
    with app.app_context():
        game = game_type(Player('human'), id='other')
        for name in ['human', 'ai1', 'ai2', 'ai3']:
            player = Player(name)
            player.player_type = Player.PlayerType.HUMAN if name == 'human' else Player.PlayerType.AI
            game.add_player(player)
        game.start_game()
        game.deal(dealer=game.players[0])
        if game_type is ContreeGame:
            game.place_bet(game.players[1], Announce('club', 80))
        monkeypatch.setitem(routes.games, 'other', game)
        client = socketio.test_client(app, namespace=routes.NAMESPACE_AI)
        try:
            result = client.emit('resume ai games', {'players': {'other': ['ai1', 'ai2', 'ai3']}},
                                 namespace=routes.NAMESPACE_AI, callback=True)
            assert result == {'ok': True, 'resumed': 1}
            [event] = client.get_received(routes.NAMESPACE_AI)
            assert event['name'] == 'player to bet'
        finally:
            client.disconnect(namespace=routes.NAMESPACE_AI)


def test_namespace_reconnect_requests_existing_ai_games(monkeypatch):
    monkeypatch.setattr(ai.this, 'game_type', 'belote', raising=False)
    monkeypatch.setattr(ai.this, 'NAMESPACE', '/belote_ai', raising=False)
    monkeypatch.setattr(ai, 'ai_players', {'reconnect': {'ai1': object(), 'ai2': object()}})
    emit = MagicMock()
    monkeypatch.setattr(ai, 'emit', emit)
    ai.namespace_connected()
    emit.assert_called_once_with('resume ai games', {'players': {'reconnect': ['ai1', 'ai2']}})


def test_delayed_move_is_discarded_after_disconnect(monkeypatch):
    timer = MagicMock()
    monkeypatch.setattr(ai.threading, 'Timer', timer)
    emit = MagicMock()
    monkeypatch.setattr(ai, 'emit', emit)
    monkeypatch.setattr(ai.this, 'NAMESPACE', '/belote_ai', raising=False)
    ai.emit_with_delay('player played', {'game_id': 'reconnect', 'card': 'h14'})
    deferred = timer.call_args.args[1]
    ai.namespace_disconnected('transport error')
    deferred()
    emit.assert_not_called()


def test_ai_play_acknowledgement_cancels_timeout(monkeypatch):
    monkeypatch.setattr(ai.this, 'mode', 'normal')
    monkeypatch.setattr(ai.this, 'NAMESPACE', '/belote_ai', raising=False)
    timer = MagicMock()
    monkeypatch.setattr(ai.threading, 'Timer', timer)
    emit = MagicMock()
    monkeypatch.setattr(ai.sio, 'emit', emit)
    data = {'game_id': 'reconnect', 'player': 'ai2', 'card': 'h14'}
    ai.emit('player played', data)
    timer.return_value.start.assert_called_once()
    emit.call_args.kwargs['callback']({'ok': True})
    timer.return_value.cancel.assert_called_once()


def test_network_send_exception_is_logged(monkeypatch, caplog):
    monkeypatch.setattr(ai.this, 'mode', 'normal')
    monkeypatch.setattr(ai.this, 'NAMESPACE', '/belote_ai', raising=False)
    monkeypatch.setattr(ai.sio, 'emit', MagicMock(side_effect=RuntimeError('disconnected')))
    ai.emit('resume ai games', {'players': {}})
    assert 'Failed to send AI event resume ai games' in caplog.text
