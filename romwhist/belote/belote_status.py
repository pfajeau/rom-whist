from enum import Enum


class BeloteStatus(str, Enum):
    Not_Allowed = "not_allowed"
    Allowed = "allowed"
    Belote_Announced = "belote_announced"
    Belote_Played = "belote_played"
    Rebelote_Announced = "rebelote_announced"
    Rebelote_Played = "rebelote_played"
    Lost = "lost"