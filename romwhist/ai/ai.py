from flask_socketio import emit
import getopt
import logging
import socketio
import sys
from ronwhist.ai.ai_player import AiPlayer

NAMESPACE = '/ohell_ai'
sio = socketio.Client()
sio.connect('http://localhost:5000', namespaces=[NAMESPACE])
app.config.from_pyfile("config_ai.py")
logging.basicConfig(filename=app.config["LOG_FILE"], \
                    format="%(asctime)s] %(levelname)s [%(filename)s  at %(lineno)s]: %(message)s", \
                    level=app.config["LOG_LEVEL"])


@sio.on('msg posted', namespace=NAMESPACE)
def msg_posted(data):
    msg = data['msg']
    print ("XXXX ai msg is: " + msg)
    if "echo" in msg:
        print("Sending echo message")
        sio.emit("client post", "Message received by AI", namespace = '/ohell')

@sio.on("new_ai_player", namespace=NAMESPACE)
def create_ai_player(data):
    game_id = data.get("game_id")
    name = data.get("name")
    if game_id is None or name is None:
        logging.error("game_id or name are not defined")
        return

    player = AiPlayer(game_id, name)
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
    print ("Emitting join game")
    AiPlayer.sio.emit("join game ai", \
                      {'player': ai_player.name, 'game_id': ai_player.game_id}, \
                      NAMESPACE)

def main(argv):
    print("In main function")
    # try:
    #     opts, args = getopt.getopt(argv, "hn:g:")
    # except getopt.GetoptError:
    #     print ('romwhist.aiplayer -n player_name -g game_id:')
    #     sys.exit(2)
    # for opt, arg in opts:
    #     print(opt)
    #     if opt == '-h':
    #         print ('romwhist.aiplayer -n player_name -g game_id:')
    #         sys.exit()
    #     elif opt == "-n":
    #         name = arg
    #     elif opt == "-g":
    #         game_id = arg
    # print (name + " " + str(game_id))
    # ai_player = AiPlayer(name, game_id)
    # ai_player.join_game()

if __name__ == "__main__":
    main(sys.argv[1:])