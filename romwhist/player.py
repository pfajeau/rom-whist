"""
This module implements player functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

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
        if other is None:
            return False
        elif isinstance(other, str):
            return self.name == other
        else:
            return self.name == other.name

    def __hash__(self):
        # return hash(str(self))
        # dump (self)
        return hash(self.name)


def dump(obj):
    for attr in dir(obj):
        print("obj.%s = %r" % (attr, getattr(obj, attr)))
    print("")