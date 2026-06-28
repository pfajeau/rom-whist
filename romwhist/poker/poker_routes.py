"""
This module implements poker routes functionality.
"""

import logging
import json

from flask import render_template, request, session, url_for, redirect, flash
from flask_babel import gettext as _
from flask_socketio import emit

from romwhist import common_routes
from romwhist import socketio
from romwhist.poker.poker_game import PokerGame
from romwhist.poker.poker_form import PokerStartForm
from romwhist.forms import LoginForm, GameForm
from romwhist.models import User
from romwhist.player import Player
from romwhist import i18n_strings
from romwhist import app


NAMESPACE = '/poker'

games = dict()
clients = dict()
messages = dict()


# ---------------------------------------------------------------------------
# HTTP routes
# ---------------------------------------------------------------------------

def poker_start():
    form = PokerStartForm()
    locale = common_routes.get_locale(request)

    if form.validate_on_submit():
        username = common_routes.sanitize_username(form.user_name.data)
        session['username'] = username

        if form.join_game.data:
            game_id = request.form['game_id']
            session['game_id'] = game_id
            return common_routes.join_game(games, game_id, username,
                                           'poker_start.html', 'poker_play',
                                           NAMESPACE, form, max_players=PokerGame.MAX_PLAYERS)

        elif form.start_game.data:
            game_id = common_routes.generate_game_id(app.config['MAX_GAMES'], games)
            if game_id is None:
                return render_template('poker_start.html',
                                       error="No more games available!!! Please try again later",
                                       form=form, locale=locale)

            logging.info("creating new poker game with id: %s", game_id)
            session['game_id'] = game_id
            poker_type = form.poker_type.data
            initial_money = form.initial_money.data
            game = PokerGame(game_creator=username, id=game_id,
                             poker_type=poker_type, initial_money=initial_money)
            games[game_id] = game
            clients[game_id] = dict()
            session['ownername'] = username
            session['poker_type'] = poker_type
            common_routes.add_player_by_name(username, game, NAMESPACE)
            common_routes.clean_old_games(games)
            return redirect(url_for('poker_play'))

    return render_template('poker_start.html', form=form, error=form.errors, locale=locale)


def poker_play():
    player_name = session.get('username')
    if player_name is None:
        logging.error("Error: username does not exist in session")
        return redirect(url_for('poker_start'))

    form = GameForm()
    game_id = session.get('game_id')
    game = games.get(game_id)
    if game is None:
        logging.info("No game found for the game id: %s", str(game_id))
        return redirect(url_for('poker_start'))

    redirect_template = common_routes.redirect_game_start(
        games, clients,
        request.form.get('action_game'),
        'poker_start',
        namespace=NAMESPACE)

    if redirect_template is None and request.method == 'POST':
        action = request.form['action_game']

        if action == 'remove_player':
            rplayer = request.form['player_list']
            common_routes.remove_player(game_id, games, clients, rplayer, NAMESPACE)
            return redirect(url_for('poker_play'))

        if action == 'restart_hand':
            deal_hands(game_id)
            return redirect(url_for('poker_play'))

        if action == 'add_ai':
            if len(game.get_playing_players()) >= PokerGame.MAX_PLAYERS:
                socketio.emit("alert", _("game_already_has_max_players"),
                              room=clients[game_id].get(player_name), namespace=NAMESPACE)
                flash(_("game_already_has_max_players"))
            else:
                common_routes.add_ai_player(len(game.players), game_id, NAMESPACE)
            return redirect(url_for('poker_play'))

        if action == 'switch_player_type':
            player = game.get_player_by_name(player_name)
            if player.player_type == Player.PlayerType.SHADOWED:
                player.player_type = Player.PlayerType.HUMAN
            elif player.player_type == Player.PlayerType.HUMAN:
                player.player_type = Player.PlayerType.SHADOWED
            return redirect(url_for('poker_play'))

    elif redirect_template is None:
        hand = game.get_hands().get(game.get_player_by_name(player_name))
        hand_cards = hand.serialize() if hand is not None else []
        active_player = game.get_active_player()
        player_obj = game.get_player_by_name(player_name)
        allowed_actions = game.get_allowed_actions(player_obj)

        if game_id not in messages:
            messages[game_id] = []

        return render_template(
            'poker.html',
            form=form,
            players=game.get_playing_players(),
            hand=hand_cards,
            community_cards=game.community_cards.serialize() if game.community_cards is not None else [],
            active_player=active_player,
            game_phase=game.phase.name,
            phase_label=game.phase.value,
            messages=json.dumps(messages[game_id]),
            i18n=json.dumps(i18n_strings.i18n()),
            player_type=player_obj.player_type.value,
            poker_type=game.poker_type,
            poker_type_label=game.get_poker_type_label(),
            embedded_game_state=game.get_state().to_json(),
            money=game.get_money(),
            pot=game.pot,
            current_bet=game.current_bet,
            bets_this_round={str(k): v for k, v in game.bets_this_round.items()},
            folded_players=[str(p) for p in game.folded_players],
            allowed_actions=allowed_actions,
            small_blind=game.small_blind,
            big_blind=game.big_blind,
        )
    else:
        return redirect(url_for('poker_start'))


# ---------------------------------------------------------------------------
# Dealing / phase helpers
# ---------------------------------------------------------------------------

def deal_hands(game_id):
    game = games.get(game_id)
    if game is None:
        logging.error("Unknown game: %s", str(game_id))
        return

    game.start_game()

    # Notify all players that the game has started (clears UI)
    common_routes.emit_to_players(
        "sc game started",
        {'nb_cards': game.hole_cards_count,
         'community_cards': [],
         'pot': game.pot,
         'bets_this_round': {},
         'small_blind': game.small_blind,
         'big_blind': game.big_blind,
         'poker_type': game.poker_type},
        room=game_id, namespace=NAMESPACE)

    # Send each player their private hole cards
    for player in game.get_playing_players():
        cards = game.get_hand(player).serialize()
        common_routes.emit_to_players(
            "new hand",
            {'game_id': game_id, 'player': str(player), 'cards': cards},
            room=clients[game_id].get(player), namespace=NAMESPACE)

    # Emit the initial phase state (PRE_FLOP) and whose turn it is
    _emit_phase_state(game_id)
    _emit_betting_turn(game_id)


def _emit_phase_state(game_id):
    """Broadcast the current phase, revealed community cards, and pot."""
    game = games.get(game_id)
    if game is None:
        return
    socketio.emit(
        'poker_phase_change',
        {'phase': game.phase.name,
         'phase_label': game.phase.value,
         'community_cards': game.community_cards.serialize() if game.community_cards else [],
         'pot': game.pot,
         'current_bet': game.current_bet,
         'bets_this_round': {str(k): v for k, v in game.bets_this_round.items()},
         'money': {str(k): v for k, v in game.money.items()}},
        room=game_id, namespace=NAMESPACE)


def _emit_betting_turn(game_id):
    """Tell all players whose turn it is and what actions are allowed."""
    game = games.get(game_id)
    if game is None or game.active_player is None:
        return
    active = game.active_player
    socketio.emit(
        'poker_to_act',
        {'player': str(active),
         'allowed_actions': game.get_allowed_actions(active),
         'current_bet': game.current_bet,
         'pot': game.pot,
         'bets_this_round': {str(k): v for k, v in game.bets_this_round.items()}},
        room=game_id, namespace=NAMESPACE)


def _do_advance_phase(game_id):
    """Advance to the next phase; emit showdown or the new phase+betting turn."""
    game = games.get(game_id)
    if game is None:
        return

    new_phase = game.advance_phase()

    if new_phase == PokerGame.GamePhase.SHOWDOWN:
        active = game.get_active_players()
        showdown_data = {
            'winners': [str(w) for w in game.hand_winners],
            'community_cards': game.community_cards.serialize() if game.community_cards else [],
            'hands': {str(p): game.get_hand(p).serialize()
                      for p in active if game.get_hand(p) is not None},
            'best_hands': {str(p): (game.get_best_hand(p).serialize()
                                    if game.get_best_hand(p) is not None else [])
                           for p in active},
            'hand_ranks': {str(p): game.get_hand_rank_description(p) for p in active},
            'money': {str(k): v for k, v in game.money.items()},
        }
        common_routes.emit_to_players(
            "poker showdown", showdown_data,
            room=game_id, namespace=NAMESPACE, game_state=game.get_state())

        game.hand_completed()
        money = {str(k): v for k, v in game.money.items()}
        socketio.emit("hand completed", {'money': money}, room=game_id, namespace=NAMESPACE)

        if game.is_game_over():
            solvent = game.get_solvent_players()
            winner = str(solvent[0]) if solvent else "Nobody"
            common_routes.emit_to_players(
                "game over", winner,
                game_id=game_id, room=game_id, namespace=NAMESPACE)
            common_routes.clean_game_data(game_id, games, clients)
        else:
            socketio.emit(
                "poker_next_hand",
                {'money': money, 'hand_nb': game._current_hand_nb},
                room=game_id, namespace=NAMESPACE)
    else:
        _emit_phase_state(game_id)
        _emit_betting_turn(game_id)


# ---------------------------------------------------------------------------
# Socket.IO handlers
# ---------------------------------------------------------------------------

@socketio.on('message', namespace=NAMESPACE)
def message(data):
    logging.debug("message received")
    common_routes.post_msg(data, session['username'], session.get('game_id'), messages, NAMESPACE)


@socketio.on('join game', namespace=NAMESPACE)
def on_join(data):
    common_routes.on_join(session.get('game_id'), games, clients, NAMESPACE)


@socketio.on('cs game started', namespace=NAMESPACE)
def cs_game_started():
    game_id = session.get('game_id')
    game = games.get(game_id)
    if game is None:
        logging.error("Unknown game id: %s", game_id)
        return
    deal_hands(game_id)


@socketio.on('poker action', namespace=NAMESPACE)
def on_poker_action(data):
    action = data.get('action')
    amount = int(data.get('amount', 0))
    game_id = session.get('game_id')
    game = games.get(game_id)
    player_name = session.get('username')

    if not game or not player_name:
        return
    player = game.get_player_by_name(player_name)
    if player is None:
        return

    ok = game.player_action(player, action, amount)
    if not ok:
        logging.warning("Invalid poker action '%s' from %s", action, player_name)
        return

    # Broadcast what happened
    socketio.emit(
        'poker_player_acted',
        {'player': player_name,
         'action': action,
         'amount': amount,
         'pot': game.pot,
         'bets_this_round': {str(k): v for k, v in game.bets_this_round.items()},
         'money': {str(k): v for k, v in game.money.items()}},
        room=game_id, namespace=NAMESPACE)

    if game.is_betting_round_complete():
        _do_advance_phase(game_id)
    else:
        _emit_betting_turn(game_id)


@socketio.on('client post', namespace=NAMESPACE)
def on_post(msg):
    common_routes.post_msg(msg, session['username'], session.get('game_id'), messages, NAMESPACE)


@socketio.on('disconnect', namespace=NAMESPACE)
def disconnect():
    common_routes.disconnect(clients)
