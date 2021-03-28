from enum import Enum


class Announce:
    def __init__(self, suit, points):
        self.suit = suit
        self.points = points

    def __str__(self):
        return self.suit + "_" + str(self.points)

    def __gt__(self, other):
        if other.points == "Capot" and self.points != "Capot":
            return False
        return self.points > other.points

    @classmethod
    def from_str(cls, announce_as_string):
        suit, points = announce_as_string.split("_", 1)
        return cls(suit, points)


class ContreStatus(str, Enum):
    NORMAL = "None"
    CONTREE = "Contree"
    SURCONTREE = "Surcontree"
