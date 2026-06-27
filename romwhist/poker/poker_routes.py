"""
This module implements poker routes functionality.
"""

import logging
import json
import threading

from flask import render_template, request, session, url_for, redirect, flash
from flask_babel import gettext as _
from flask_login import current_user, login_user
from flask_socketio import emit

from romwhist import common_routes
from romwhist import socketio
from romwhist.poker.poker_game import PokerGame
from romwhist.poker.poker_form import PokerStartForm
from romwhist.extensions import db
from romwhist.forms import LoginForm, GameForm
from romwhist.models import User
from romwhist.player import Player
from romwhist import i18n_strings
from romwhist import app


NAMESPACE = '/poker'

# Map of games, key is game id
games = dict()

# Dictionary of session iDs for each game. This is a dictionary of Dictionary
# Keys are game ids and then player ids. Used for socketio.
clients = dict()

# Dictionary of messages for each game
messages = dict()


# @app.route("/poker_start",methods=['GET', 'POST'])
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
                return render_template('poker_start.html', error="No more games available!!! Please try again later",
                                       form=form, locale=locale)

            logging.info("creating new poker game with id: %s", game_id)
            session['game_id'] = game_id
            poker_type = form.poker_type.data
            game = PokerGame(game_creator=username, id=game_id, poker_type=poker_type)
            games[game_id] = game
            clients[game_id] = dict()
            session['ownername'] = username
            session['poker_type'] = poker_type
            common_routes.add_player_by_name(username, game, NAMESPACE)
            common_routes.clean_old_games(games)
            return redirect(url_for('poker_play'))

    return render_template('poker_start.html', form=form, error=form.errors, locale=locale)


# @app.route("/poker_play", methods=['GET', 'POST'])
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
        games,
        clients,
        request.form.get('action_game'),
        'poker_start',
        namespace=NAMESPACE)

    if redirect_template is None and request.method == 'POST':
        if request.form['action_game'] == 'remove_player':
            rplayer = request.form['player_list']
            common_routes.remove_player(game_id, games, clients, rplayer, NAMESPACE)
            return redirect(url_for('poker_play'))

        if request.form['action_game'] == 'restart_hand':
            deal_hands(game_id)
            return redirect(url_for('poker_play'))

        if request.form['action_game'] == 'add_ai':
            if len(game.get_playing_players()) >= PokerGame.MAX_PLAYERS:
                socketio.emit("alert", _("game_already_has_max_players"),
                              room=clients[game_id].get(player_name), namespace=NAMESPACE)
                flash(_("game_already_has_max_players"))
            else:
                common_routes.add_ai_player(len(game.players), game_id, NAMESPACE)
            return redirect(url_for('poker_play'))

        if request.form['action_game'] == 'switch_player_type':
            player = game.get_player_by_name(player_name)
            if player.player_type == Player.PlayerType.SHADOWED:
                player.player_type = Player.PlayerType.HUMAN
            elif player.player_type == Player.PlayerType.HUMAN:
                player.player_type = Player.PlayerType.SHADOWED
            return redirect(url_for('poker_play'))

    elif redirect_template is None:
        hand = game.get_hands().get(game.get_player_by_name(player_name))
        hand_cards = hand.serialize() if hand is not None else []
        cards_played = game.get_cards_played_current_round()
        active_player = game.get_active_player()

        if game_id not in messages:
            messages[game_id] = []

        return render_template('poker.html', form=form, players=game.get_playing_players(), scores=game.get_scores(),
                               hand=hand_cards, wins=game.wins, active_player=active_player,
                               cards_played=cards_played, allowed_cards=json.dumps(game.get_allowed_cards(active_player)),
                               game_phase=game.phase.name, messages=json.dumps(messages[game_id]),
                               i18n=json.dumps(i18n_strings.i18n()),
                               player_type=game.get_player_by_name(player_name).player_type.value,
                               poker_type=game.poker_type,
                               poker_type_label=game.get_poker_type_label(),
                               embedded_game_state=game.get_state().to_json())

    else:
        return redirect(url_for('poker_start'))


def deal_hands(game_id):
    game = games.get(game_id)
    if game is None:
        logging.error("Unknown game: %s", str(game_id))
        return

    game.start_game()
    common_routes.emit_to_players("sc game started", {'nb_cards': game.hand_size},
                                  room=game_id, namespace=NAMESPACE)

    for player in game.get_playing_players():
        cards = game.get_hand(player).serialize()
        common_routes.emit_to_players(
            "new hand",
            {'game_id': game_id, 'player': player, 'cards': cards},
            room=clients[game_id].get(player), namespace=NAMESPACE)

    showdown_data = {
        'winners': [player.name for player in game.hand_winners],
        'hands': {player.name: game.get_hand(player).serialize() for player in game.get_playing_players()},
        'hand_ranks': {player.name: game.get_hand_rank_description(player) for player in game.get_playing_players()}
    }

    common_routes.emit_to_players(
        "poker showdown",
        showdown_data,
        room=game_id, namespace=NAMESPACE, game_state=game.get_state())

    game.hand_completed()
    hand_completed(game_id)


def hand_completed(game_id):
    game = games.get(game_id)
    if game is None:
        logging.error("Game with id %s does not exist", game_id)
        return

    game.hand_completed()
    scores = game.get_scores()
    socketio.emit("hand completed", {'scores': scores, 'wins': game.wins,
                                       'hand_nb': game._current_hand_nb,
                                       'player_to_deal': game.next_player_to_deal()},
                  room=game_id, namespace=NAMESPACE)

    if game.is_game_over():
        common_routes.emit_to_players(
            "game over",
            game.get_highest_score_player(), game_id=game_id,
            room=game_id, namespace=NAMESPACE)
        common_routes.clean_game_data(game_id, games, clients)


def next_round(game_id, nplayer, allowed_cards):
    game = games[game_id]
    common_routes.next_round(game, nplayer, allowed_cards, hand_completed, NAMESPACE)


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


@socketio.on('player played', namespace=NAMESPACE)
def player_played(card):
    logging.info("card played event received")
    game_id = session.get('game_id')
    game = games.get(game_id)
    player_name = session.get('username')
    player = game.get_player_by_name(player_name)

    if game is None or player is None:
        return {'ok': False, 'error': 'unknown_game_or_player'}

    if game.get_active_player() != player:
        logging.warning("Play rejected: not %s's turn", player_name)
        return {'ok': False, 'error': 'not_your_turn'}

    allowed = game.get_allowed_cards(player)
    if allowed and card not in allowed:
        logging.warning("Play rejected: illegal card %s for %s", card, player_name)
        return {'ok': False, 'error': 'illegal_card'}

    try:
        winner = game.play_card(player, card)
    except Exception:
        logging.exception("play_card failed")
        return {'ok': False, 'error': 'server_error'}

    common_routes.emit_to_players(
        "card played",
        {'game_id': game_id, 'player': player, 'card': card},
        room=game_id, namespace=NAMESPACE)

    nplayer = game.get_active_player()
    if winner is None:
        common_routes.emit_to_players(
            "player to play",
            {'game_id': game_id, 'player': nplayer, 'allowed_cards': game.get_allowed_cards(nplayer), 'last_player': player},
            room=game_id, namespace=NAMESPACE, game_state=game.get_state())
    else:
        allowed_cards = game.get_hand(nplayer).serialize() if nplayer is not None else []
        winning_card = game.get_current_round().cards_played[winner]
        common_routes.emit_to_players(
            "round ended",
            {"game_id": game_id, "winner": winner, "card": winning_card.desc(), "last_player": player,
             "points": game.wins},
            room=game_id, namespace=NAMESPACE)

        threading.Timer(6.0, next_round, [game_id, nplayer, allowed_cards]).start()

    logging.info("Allowed cards: %s", str(allowed_cards))
    return {'ok': True}


@socketio.on('client post', namespace=NAMESPACE)
def on_post(msg):
    common_routes.post_msg(msg, session['username'], session.get('game_id'), messages, NAMESPACE)


@socketio.on('disconnect', namespace=NAMESPACE)
def disconnect():
    common_routes.disconnect(clients)
