class AiPlayer:

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
