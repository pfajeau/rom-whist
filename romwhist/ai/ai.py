import configparser
import getopt
import logging
import sys
import threading

import socketio
from flask_socketio import emit
from romwhist.belote.belote_ai import BeloteAiPlayer
from romwhist.ohell.ohell_ai import OhellAiPlayer
from romwhist.contree.contree_ai import ContreeAiPlayer

NAMESPACES = {'ohell': '/ohell_ai',
              'belote': '/belote_ai',
              'contree': '/contree_ai'}

this = sys.modules[__name__]
sio = socketio.Client()

config = configparser.ConfigParser()
config.read('instance/config_ai.ini')
log_levels = {"DEBUG": logging.DEBUG, "INFO": logging.INFO, "WARNING": logging.WARNING, "ERROR": logging.ERROR}
logging_config = config['logging']
log_level = logging_config["LOG_LEVEL"]
logging.basicConfig(filename=logging_config["LOG_FILE"],
                    format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s",
                    level=log_levels[log_level])

network_config = config['network']
HOST = network_config["host"]

if config.has_section('ai'):
    ai_config = config['ai']
    if config.has_option('ai','default_delay'):
        DEFAULT_DELAY = int(ai_config['default_delay'])
    else:
        DEFAULT_DELAY = 2  # 1 second



# List of ai players for each game. it is a list of lists
players = dict()


# @sio.on('trump card', namespace=NAMESPACE)
def trump_card(data):
    logging.info("trump card event received")
    game_id = data.get('game_id')
    trump_card = data.get('trump_card')
    trump_suit = data.get("trump_suit")
    ai_players = get_players(game_id)
    for ai_player_name in ai_players:
        ai_player = get_player(game_id, ai_player_name)
        ai_player.set_trump(trump_card, trump_suit)


# @sio.on('sc game started', namespace=NAMESPACE)
def game_started(data):
    logging.info("sc game started event received")
    game_id = data.get('game_id')
    deck_size = data.get('deck_size')
    players = data.get('players')
    ai_players = get_players(game_id)
    for ai_player_name in ai_players:
        ai_player = get_player(game_id, ai_player_name)
        ai_player.game_started(deck_size, players)


# @sio.on('new hand', namespace=NAMESPACE)
def new_hand(data):
    logging.info("new hand event received")
    game_id = data.get('game_id')
    player = data.get('player')
    cards = data.get('cards')
    ai_players = get_players(game_id)
    for ai_player_name in ai_players:
        if ai_player_name == player:
            ai_player = get_player(game_id, player)
            ai_player.new_hand(cards)


# @sio.on('player to bet', namespace=NAMESPACE)
def player_to_bet(data):
    logging.info("player to bet event received")
    game_id = data.get('game_id')
    player = data.get('player')
    game_state_json = data['state']

    ai_player = get_player(game_id, player)

    logging.debug("PLayer to bet: %s - game_id: %s", player, game_id)

    if ai_player is not None:
        bet = ai_player.player_to_bet(data.get("allowed_bets"), game_state_json)
        emit_with_delay('player bet', {'game_id': game_id, 'player': player, 'bet': bet})


def player_bet(data):
    logging.info("player bet event received")
    game_id = data.get('game_id')
    player = data.get('player')
    bet = data.get('bet')
    ai_players = get_players(game_id)
    for ai_player_name in ai_players:
        ai_player = get_player(game_id, ai_player_name)
        ai_player.player_bet(player, bet)


# @sio.on('player to play', namespace=NAMESPACE)
def player_to_play(data):
    logging.info("player to play event received")
    game_id = data.get('game_id')
    player = data.get('player')
    game_state_json = data['state']

    ai_player = get_player(game_id, player)
    logging.debug("PLayer to play: %s - game_id: %s", player, game_id)

    if ai_player is not None:
        card = ai_player.player_to_play(data.get("allowed_cards"), game_state_json)
        emit_with_delay('player played', {'game_id': game_id, 'player': player, 'card': card})


# @sio.on('card played', namespace=NAMESPACE)
def card_played(data):
    logging.info("card played event received")
    game_id = data.get('game_id')
    card = data.get('card')
    player = data.get('player')
    ai_players = get_players(game_id)
    for ai_player_name in ai_players:
        ai_player = get_player(game_id, ai_player_name)
        ai_player.card_played(player, card)


def game_over(datq):
    # TODO
    logging.info("game over event received")


def game_state(data):
    logging.info("game_state event received")
    game_id = data.get('game_id')
    player = data.get('player')
    state_as_json = data.get('state')

    ai_player = get_player(game_id, player)

    if ai_player is not None:
        ai_player.set_game_state_from_json(state_as_json)


# @sio.on('msg posted', namespace=NAMESPACE)
def msg_posted(data):
    msg = data['msg']
    print("XXXX ai msg is: " + msg)
    if "echo" in msg:
        print("Sending echo message")
        sio.emit("client post", "Message received by AI", namespace=NAMESPACE)


# @sio.on("create_ai_player", namespace=NAMESPACE)
def create_ai_player(data):
    logging.info("In create_ai_player")
    game_id = data.get("game_id")
    name = data.get("name")
    if game_id is None or name is None:
        logging.error("game_id or name are not defined")
        return

    if this.game_type == "belote":
        player = BeloteAiPlayer(name, game_id)
    elif this.game_type == "ohell":
        player = OhellAiPlayer(name, game_id)
    elif this.game_type == "contree":
        player = ContreeAiPlayer(name, game_id)

    if players.get(game_id) is None:
        players[game_id] = dict()

    # TODO: handle case where player already exists in set
    players[game_id][name] = player
    join_game(player)


@sio.event
def connect():
    print("I'm connected!")


@sio.event
def connect_error():
    print("The connection failed!")


@sio.event
def disconnect():
    print("I'm disconnected!")


def join_game(ai_player):
    print("Emitting join game")
    emit("join game ai",
         {'player': ai_player.name, 'game_id': ai_player.game_id})


def get_player(game_id, player_name):
    if game_id is None:
        logging.error("game_id misssing")
        return None
    ai_player = players.get(game_id).get(player_name)
    return ai_player


def get_players(game_id):
    if game_id is None:
        logging.error("game_id misssing")
        return None
    ai_players = players.get(game_id)
    return ai_players


def emit_with_delay(event, data, delay=DEFAULT_DELAY):
    timer = threading.Timer(delay, emit, [event, data])
    timer.start()


def emit(event, data):
    sio.emit(event, data, namespace=NAMESPACE)


def main(argv):
    print("In main function")
    try:
        opts, args = getopt.getopt(argv, "hg:")
    except getopt.GetoptError:
        print('romwhist.aiplayer -g game')
        sys.exit(2)
    for opt, arg in opts:
        print(opt)
        if opt == '-h':
            print('ai -g game. E.g. ai -g belote or ai -g ohell')
            sys.exit()
        elif opt == "-n":
            name = arg
        elif opt == "-g":
            this.game_type = arg
            this.NAMESPACE = NAMESPACES[this.game_type]

    sio.connect(HOST, namespaces=[this.NAMESPACE])
    sio.on("create_ai_player", create_ai_player, this.NAMESPACE)
    sio.on("sc game started", game_started, this.NAMESPACE)
    sio.on("trump card", trump_card, this.NAMESPACE)
    sio.on("new hand", new_hand, this.NAMESPACE)
    sio.on("player to bet", player_to_bet, this.NAMESPACE)
    sio.on("player bet", player_bet, this.NAMESPACE)
    sio.on("player to play", player_to_play, this.NAMESPACE)
    sio.on("card played", card_played, this.NAMESPACE)
    sio.on("game over", game_over, this.NAMESPACE)
    sio.on("game_state", game_state, this.NAMESPACE)

    # print (name + " " + str(game_id))
    # ai_player = AiPlayer(name, game_id)
    # ai_player.join_game()


if __name__ == "__main__":
    main(sys.argv[1:])
