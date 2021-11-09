"""
This module implements routes.

author: Philippe Fajeau

"""
import logging
import threading
import json
from random import randint

from flask import render_template, request, flash, session, url_for, redirect
from flask_babel import gettext as _
# from flask import Blueprint

from flask_login import current_user, login_user
from flask_socketio import emit

from romwhist import common_routes
from romwhist.card import Card
from romwhist import socketio
from romwhist.contree.contree import ContreeGame, CountingMethod
from romwhist.contree.announce import Announce
from romwhist.belote.belote_status import BeloteStatus
from romwhist.belote.belote import BeloteGame
from romwhist.contree.contree_form import ContreeStartForm
from romwhist.extensions import db
from romwhist.forms import LoginForm, GameForm
from romwhist.models import User
from romwhist import i18n_strings
from romwhist.belote import belote_routes

NAMESPACE = '/contree'
NAMESPACE_AI = '/contree_ai'

# Map of games, key is game id
games = dict()

# Dictionary of session iDs for each game. This is a dictionary of Dictionary
# Keys are game ids and then player ids. Used for socketio.
clients = dict()

# Dictionary of messages for each game
messages = dict()


# @app.route("/contree_start",methods=['GET', 'POST'])
def contree_start():
    form = ContreeStartForm()
    locale = common_routes.get_locale(request)
    logging.info("Language set to: %s", locale)

    if form.validate_on_submit():
        # Sanitize the username (as it used as IDs in the html)
        username = common_routes.sanitize_username(form.user_name.data)
        logging.debug("User: " + username)

        # Used by client
        previous_alias = session.get('username')

        session['username'] = username
        if form.join_game.data:
            game_id = request.form['game_id']
            session['game_id'] = game_id
            return common_routes.join_game(games, game_id, username,
                                           'contree_start.html', 'contree_play',
                                           NAMESPACE, form, max_players=4)

        elif form.start_game.data:
            logging.info("start game")
            game_id = common_routes.generate_game_id(999, games)
            if game_id is None:
                return render_template('contree_start.html',
                                       error="No more games available!!! Please try again later",
                                       form=form, locale=locale)

            points_to_reach = int(form.points_to_reach.data)
            # index = int(form.counting.data)
            # counting_str = form.counting.choices[index][1]
            counting_str = form.counting.data
            logging.debug("Counting string from UI: %s", counting_str)
            counting = CountingMethod(counting_str)
            logging.debug("Counting: %s", counting)

            logging.info("creating new game with id: " + str(game_id))
            # Add game id in session
            game = ContreeGame(game_creator=username, id=game_id, counting=counting)
            game.win_game_points = points_to_reach

            games[game_id] = game
            # players[game_id] = []
            clients[game_id] = dict()

            # dealing_method = request.form['dealing_method']
            # logging.info ("In route game, dealing method is: ", request.form['dealing_method'])
            session['ownername'] = username
            add_player(username, game_id)
            return redirect(url_for('contree_play'))
    else:
        return render_template("contree_start.html", form=form,
                               error=form.errors, locale=locale)


# @app.route("/contree_play", methods=['GET', 'POST'])
def contree_play():
    logging.info("In contree_play route")
    form = GameForm()
    player = session.get('username')
    game_id = session.get('game_id')
    game = games.get(game_id)

    redirect_template = common_routes.redirect_game_start(
        games,
        clients,
        request.form.get('action_game'),
        'contree_start',
        namespace=NAMESPACE)

    if redirect_template is None and request.method == 'POST':
        if request.form['action_game'] == "remove_player":
            logging.info("Remove Player button pressed")
            rplayer = request.form['player_list']
            logging.info("Player to remove: " + rplayer)

            remove_player(game_id, rplayer)
            return redirect(url_for('contree_play'))

        if request.form['action_game'] == "restart_hand":
            restart_hand(game_id)
            return redirect(url_for('contree_play'))

        if request.form['action_game'] == "add_ai":
            if len(game.get_playing_players()) >= BeloteGame.MAX_PLAYERS:
                socketio.emit("alert", _("game_already_has_max_players"),
                              room=clients[game_id].get(player), namespace=NAMESPACE)
                flash(_("game_already_has_max_players"))
            else:
                common_routes.add_ai_player(len(game.players),
                                            game_id, NAMESPACE_AI)
            return redirect(url_for('contree_play'))
        print("No matching action!!!!!")
        return redirect(url_for('contree_start'))

    elif redirect_template is None or request.method == 'GET':
        hand = game.get_hands().get(player)
        if hand is None:
            hand = []
        else:
            hand = hand.serialize()

        cards_played = game.get_cards_played_current_round()

        logging.debug("Game Phase: " + game.phase.name)
        active_player = game.get_active_player()

        bets_suit = dict()
        bets_points = dict()
        for player in game.get_playing_players():
            bets_suit[player] = game.bets[player].suit
            bets_points[player] = game.bets[player].points

        if game_id not in messages:
            messages[game_id] = []

        # TODO: could pass the game state instead of all the parameters
        # individually
        return render_template("contree.html", form=form, players=game.get_playing_players(), scores=game.get_scores(),
                               hand=hand, wins=game.hand_points, bets_suit=bets_suit, bets_points=bets_points,
                               active_player=active_player,
                               cards_played=cards_played, allowed_cards=json.dumps(game.get_allowed_cards(active_player)),
                               trump=game.trump_card, trump_suit=game.trump_suit,
                               allowed_bets=game.get_allowed_bets(player),
                               game_phase=game.phase.name, scoresheet=game.scoresheet,
                               belote_status=game.belote_status.value, player_with_belote=game.player_with_belote,
                               contree_status=game.contree_status.value, current_bet=game.current_bet,
                               taker=game.taker, i18n=json.dumps(i18n_strings.i18n()),
                               player_type = player.player_type.value,
                               messages=json.dumps(messages[game_id]))
    else:
        # Should never happen
        return redirect(url_for('contree_start'))


# @app.route("/login",methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('contree_start'))
    form = LoginForm()
    if form.validate_on_submit():
        logging.debug("User name from form:" + form.username.data)
        user = User.query.filter_by(form.username.data).first()
        if user is None:
            user = User(form.username.data)
            db.session.add(user)
            db.session.commit()
        login_user(user, remember=form.remember_me.data)
        logging.debug("current user: " + session['username'])
        return redirect(url_for("contree_start"))
    return render_template('login.html', title='Sign In', form=form)


@socketio.on("cs game started", namespace=NAMESPACE)
def game_started():
    game_id = session.get('game_id')
    if game_id is not None:
        game = games.get(game_id)
        if game is not None:
            game.reset()
            game.start_game()
            player = game.get_playing_players()[randint(0, len(game.get_playing_players()) - 1)]
            common_routes.emit_to_players(
                "sc game started",
                {'game_id': game_id, 'player_to_deal': player, 'deck_size': game.deck_size},
                room=game_id, namespace=NAMESPACE)

            generate_hands(game_id, player)


@socketio.on("player bet", namespace=NAMESPACE_AI)
def player_bet_ai(data):
    logging.debug("player bet event received for ai")
    logging.debug("Player bet: " + str(data.get('bet')))
    player = data.get('player')
    bet = data.get('bet')
    bet = Announce(bet['suit'], bet['points'])

    game_id = data.get('game_id')
    # bet_suit = data.get('bet_suit')
    # bet_points = data.get('bet_points')
    # bet = Announce(bet_suit, bet_points)
    player_bet_process(player, game_id, bet)


@socketio.on("player bet", namespace=NAMESPACE)
def player_bet(bet_suit, bet_points):
    logging.info("player bet event received")
    bet = Announce(bet_suit, bet_points)
    logging.info("Player bet: %s %s", bet_suit, bet_points)
    player = session.get('username')
    game_id = session.get('game_id')

    player_bet_process(player, game_id, bet)
    return


def player_bet_process(player, game_id, bet):
    if game_id is None:
        logging.error("ERROR: Game not found!!!")
        return

    logging.debug("Player bet: %s", bet)
    game = games.get(game_id)
    if game.phase == BeloteGame.GamePhase.BET:
        try:
            game.place_bet(player, bet)

            # There is a case where actual_bet and bet will be different (surcontre)
            actual_bet = game.bets[player]
            common_routes.emit_to_players(
                "player bet",
                {'game_id': game_id, 'player': player, 'bet_suit': actual_bet.suit,
                 'bet_points': actual_bet.points, 'taker': game.taker,
                 'current_bet': game.current_bet, 'contree_status': game.contree_status},
                room=game_id, namespace=NAMESPACE)

            nplayer = game.get_active_player()
            if game.phase == BeloteGame.GamePhase.DEAL:
                restart_hand(game_id)

            elif game.phase == BeloteGame.GamePhase.BET:
                common_routes.emit_to_players(
                    "player to bet",
                    {'game_id': game_id, 'player': nplayer, 'allowed_bets': game.get_allowed_bets(nplayer)},
                    room=game_id, namespace=NAMESPACE, game_state=game.get_state())

            elif game.phase == BeloteGame.GamePhase.PLAY:
                game.create_round()
                # Distribute cards to each players
                for player in game.get_playing_players():
                    cards = game.hands[player].serialize()
                    logging.debug("Cards for player " + player + " " + str(cards))
                    common_routes.emit_to_players(
                        "new hand",
                        {'game_id': game_id, 'player': player, 'cards': cards},
                        room=clients[game_id].get(player), namespace=NAMESPACE)
                next_player_to_play = game.get_active_player()
                allowed_cards = game.get_hand(next_player_to_play).serialize()
                logging.debug("Allowed cards: " + str(allowed_cards))
                logging.debug("Player to play: " + next_player_to_play)

                common_routes.emit_to_players(
                    "trump suit",
                    game.trump_suit, game_id=game_id, room=game_id, namespace=NAMESPACE)

                common_routes.emit_to_players(
                    "player to play",
                    {'game_id': game_id, 'player': next_player_to_play, 'allowed_cards': allowed_cards},
                    room=game_id, namespace=NAMESPACE, game_state=game.get_state())

                player_belote = game.player_with_belote
                if player_belote is not None:
                    logging.debug("Player with Belote / Rebelote: " + player_belote)
                    common_routes.emit_to_players(
                        "belote rebelote enabled",
                        player_belote, game_id=game_id,
                        room=clients[game_id].get(player_belote), namespace=NAMESPACE)
            return
        except Exception as e:
            logging.warning("Bet received: " + str(bet))
            logging.error(e)
            common_routes.emit_to_players(
                "player to bet",
                {'game_id': game_id, 'player': game.get_active_player(),
                 'allowed_bets': game.get_allowed_bets(game.get_active_player())},
                room=game_id, namespace=NAMESPACE, game_state=game.get_state())

            emit("alert", "Error in place bet", room=clients[game_id].get(player), namespace=NAMESPACE)


# TODO: this could be factorized in common routes.
def hand_completed(game_id, username):
    game = games.get(game_id)
    if game is None:
        logging.error("Game with id %s does not exist", game_id)
        return

    # TODO: Is this call needed?
    game.hand_completed()
    scores = game.get_scores()
    logging.info("hand completed, next player to deal:" + game.next_player_to_deal())
    socketio.emit("hand completed", {'scores': scores, 'wins': game.hand_points,
                                     'hand_nb': game._current_hand_nb, 'player_to_deal': game.next_player_to_deal(),
                                     'winners': game.hand_winner},
                  room=game_id, namespace=NAMESPACE)

    if game.is_game_over():
        logging.debug("Game " + str(game_id) + " is over")
        common_routes.emit_to_players(
            "game over",
            game.get_highest_score_player(), game_id=game_id,
            room=game_id, namespace=NAMESPACE)
        logging.debug("Game " + str(game_id) + " is over")

        # Need a timer here so that game is cleared after a bit
        timer = threading.Timer(5.0, clean_game_data, [game_id])
        timer.start()
        # clean_game_data(game_id)

    else:
        generate_hands(game_id, "")


def next_round(game_id, nplayer, allowed_cards):
    game = games[game_id]
    common_routes.next_round(game, nplayer, allowed_cards, hand_completed, NAMESPACE)


@socketio.on('player played', namespace=NAMESPACE_AI)
def player_played_ai(data):
    logging.debug("player played event received for ai")
    logging.debug("Player card: " + data.get('card'))
    logging.debug("Game id: " + data.get('game_id'))
    player = data.get('player')
    game_id = data.get('game_id')
    card = data.get('card')
    game = games.get(game_id)

    # Announce belote / rebelote as applicable
    common_routes.belote_rebelote_ai(game, card, player, NAMESPACE)
    belote_routes.player_played_process(game_id, player, card)


@socketio.on('player played', namespace=NAMESPACE)
def player_played(card):
    logging.info("card played event received")
    logging.info("Card played: " + card)
    game_id = session.get('game_id')
    game = games.get(game_id)
    player = session.get('username')
    player_played_process(game_id, player, card)


# TODO: function can be moved to common_routes as it is the same as the belote
# routes one
def player_played_process(game_id, player, card):
    # Emit event to players so they can see the card that was played
    if game_id is None:
        logging.error("Game id not specified")
        return

    game = games.get(game_id)
    belote_before = game.belote_status
    winner = game.play_card(player, card)

    common_routes.emit_to_players(
        "card played",
        {'game_id': game_id, 'player': player, 'card': card},
        room=game_id, namespace=NAMESPACE)

    belote_after = game.belote_status

    if belote_before != belote_after:
        belote_status_changed(game_id)

    nplayer = game.get_active_player()

    if winner is None:
        # Round continues
        allowed_cards = game.get_allowed_cards(nplayer)
        common_routes.emit_to_players(
            "player to play",
            {'game_id': game_id, 'player': nplayer, 'allowed_cards': allowed_cards, "last_player": player},
            room=game_id, namespace=NAMESPACE, game_state=game.get_state())
    else:
        # There is a winner, so round is ended
        # game.round_ended(winner)
        allowed_cards = game.get_hand(nplayer).serialize()
        winning_card = game.get_current_round().cards_played[winner]
        common_routes.emit_to_players(
            "round ended",
            {"game_id": game_id, "winner": winner, "card": winning_card.desc(),
             "last_player": player, "points": game.hand_points},
            room=game_id, namespace=NAMESPACE)

        timer = threading.Timer(6.0, next_round, [game_id, nplayer, allowed_cards])
        timer.start()

    logging.info("Allowed cards: " + str(allowed_cards))
    return


def belote_status_changed(game_id):
    game = games[game_id]
    common_routes.belote_status_changed(game_id, game, NAMESPACE)
    return


# TODO factorize with ohell
def generate_hands(game_id, username, nbcards=5, trump=True):
    game = games.get(game_id)
    if game is None:
        logging.error("Unknown game: " + str(game_id))
        return

    hands = game.deal(username)

    # FInd out who the first player to bet is
    nplayer = game.get_active_player()

    # Distribute cards to each players
    for player in game.get_playing_players():
        cards = hands[player].serialize()
        logging.info("Cards for player " + player + " " + str(cards))
        common_routes.emit_to_players(
            "new hand",
            {'game_id': game_id, 'player': player, 'cards': cards},
            room=clients[game_id].get(player), namespace=NAMESPACE)

    # common_routes.emit_to_players(
    #     "trump card",
    #     {"game_id": game_id, "trump_card": str(game.trump_card), "trump_suit": str(game.trump_suit)},
    #     room=game_id, namespace=NAMESPACE)

    common_routes.emit_to_players(
        "player to bet",
        {'game_id': game_id, 'player': nplayer, 'allowed_bets': game.get_allowed_bets(nplayer)},
        room=game_id, namespace=NAMESPACE, game_state=game.get_state())
    return


@socketio.on('belote announced', namespace=NAMESPACE)
def belote_announced(announce):
    common_routes.belote_announced(announce, games, NAMESPACE)
    return


@socketio.on('join game', namespace=NAMESPACE)
def on_join(data):
    common_routes.on_join(session.get('game_id'), games, clients, NAMESPACE)
    return


@socketio.on('join game ai', namespace=NAMESPACE_AI)
def join_ai(data):
    game_id = str(data.get('game_id'))
    player = data.get('player')
    common_routes.join_ai(game_id, player, games, NAMESPACE)
    return


@socketio.on('client post', namespace=NAMESPACE)
def on_post(msg):
    # Just distribute to players in room
    common_routes.post_msg(msg, session['username'], session.get('game_id'),
                           messages, NAMESPACE)


@socketio.on('disconnect', namespace=NAMESPACE)
def disconnect():
    common_routes.disconnect(clients)
    return


def check_player_left(player, game_id, client_id):
    # If the player still exist with a client_id that has not changed
    # it means that the player has closed the browser window or
    # something similar. In this case, the player has to be removed
    # from the game. If the client_id has changed, it just mean
    # a refresh page has happened, so leave the player in the game

    # Do nothing, let game owner remove user manually if needed
    players = clients.get(game_id)
    if players is None:
        return

    # if player in players:
    #     current_client_id = clients[game_id][player]
    #     if current_client_id == client_id:
    # remove_player(game_id, player)


def restart_hand(game_id):
    game = games.get(game_id)
    if game is None:
        return
    socketio.emit("alert", _("hand_to_be_replayed"), room=game_id, namespace=NAMESPACE)
    if game.started:
        # Deal another hand
        game._current_hand_nb = game._current_hand_nb - 1
        generate_hands(game.id, game.dealer)


# Add player to a game
def add_player(player, game_id):
    game = games.get(game_id)
    if game is not None:
        if len(game.get_playing_players()) >= 4:
            logging.error("Max number of players reached")
            return None
        else:
            session['game_id'] = game.id
            common_routes.add_player(player, game, NAMESPACE)
            if game.started:
                restart_hand(game_id)
            return player


def remove_player(game_id, player):
    common_routes.remove_player(game_id, games, clients, player, NAMESPACE)
    restart_hand(game_id)


def clean_game_data(game_id):
    common_routes.clean_game_data(game_id, games, clients)


# e.g blueprint and routes
# auth_blueprint = Blueprint("auth", "auth", url_prefix="/auth")
# auth_blueprint.add_url_rule("register", "register", controllers.register)
