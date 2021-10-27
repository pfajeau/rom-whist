from enum import Enum
import logging


class Player(str):

    class PlayerStatus(str, Enum):
        ACTIVE = "Active"
        INACTIVE = "Inactive"

    class PlayerType(str, Enum):
        HUMAN = "Human"
        AI = "AI"
        SHADOWED = "Shadowed"

    def __init__(self, name):
        # str.__init__(self)
        # super().__init__()

        self.__player_status = Player.PlayerStatus.ACTIVE
        self.__player_type = Player.PlayerType.HUMAN
        self.name = name

    @property
    def player_status(self):
        return self.__player_status

    @player_status.setter
    def player_status(self, value):
        self.__player_status = value

    @property
    def player_type(self):
        return self.__player_type

    @player_type.setter
    def player_type(self, value):
        self.__player_type = value

    def __str__(self):
        return self.name

    def __eq__(self, other):
        print("Comparing " + self.name + " with " + str(other))
        print ("Other type: " + str(type(other)))
        if other is None:
            return False
        return self.name == other.name

    def __hash__(self):
        # return hash(str(self))
        return hash(self.name)
