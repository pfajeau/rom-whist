from flask_socketio import emit
import socketio
import sys
import getopt

class AiPlayer:
    NAMESPACE = '/ohell'
    sio = socketio.Client()
    sio.connect('http://localhost:5000', namespaces=[NAMESPACE])
    print("Bla")

    def __init__(self, name, game_id):
        self.__name = name
        self.__game_id = game_id
        print("Hello World!")

    @property
    def name(self):
        return self.__name

    @name.setter
    def name(self, value):
        self.__name = value

    @property
    def game_id(self):
        return self.__game_id

    @game_id.setter
    def game_id(self, value):
        self.__game_id = value

    @sio.on('msg posted', namespace='/ohell')
    def msg_posted(data):
        msg = data['msg']
        print ("XXXX In AI player, msg is: " + msg)
        if "echo" in msg:
            print("Sending echo message")
            AiPlayer.sio.emit("client post", "Message received by AI", namespace = '/ohell')


    @sio.event
    def connect():
        print("I'm connected!")

    @sio.event
    def connect_error():
        print("The connection failed!")

    @sio.event
    def disconnect():
        print("I'm disconnected!")

    def join_game(self):
        print ("Emitting join game")
        AiPlayer.sio.emit("join game ai", \
                          {'player': self.name, 'game_id': self.game_id}, \
                          AiPlayer.NAMESPACE)

def main(argv):
    print("In main function")
    try:
        opts, args = getopt.getopt(argv, "hn:g:")
    except getopt.GetoptError:
        print ('romwhist.aiplayer -n player_name -g game_id:')
        sys.exit(2)
    for opt, arg in opts:
        print(opt)
        if opt == '-h':
            print ('romwhist.aiplayer -n player_name -g game_id:')
            sys.exit()
        elif opt == "-n":
            name = arg
        elif opt == "-g":
            game_id = arg
    print (name + " " + str(game_id))
    ai_player = AiPlayer(name, game_id)
    ai_player.join_game()

if __name__ == "__main__":
    main(sys.argv[1:])