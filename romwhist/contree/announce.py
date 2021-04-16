from enum import Enum

class Announce(dict):
    def __init__(self, suit, points):
        dict.__init__(self, suit=suit, points=points)
        self.suit = suit
        if points == "Capot":
            # TODO: constant should be defined in another module
            self.points = 162
        else:
            self.points = int(points)

    def __str__(self):
        return self.suit + "_" + str(self.points)

    def __gt__(self, other):
        if other.points == "Capot" and self.points != "Capot":
            return False
        return int(self.points) > int(other.points)

    @classmethod
    def from_str(cls, announce_as_string):
        if announce_as_string == "":
            return None
        else:
            suit, points = announce_as_string.split("_", 1)
            return cls(suit, points)


class ContreStatus(str, Enum):
    NORMAL = "None"
    CONTREE = "Contree"
    SURCONTREE = "Surcontree"
