"""
This module implements belote status functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from enum import Enum


class BeloteStatus(str, Enum):
    Not_Allowed = "not_allowed"
    Allowed = "allowed"
    Belote_Announced = "belote_announced"
    Belote_Played = "belote_played"
    Rebelote_Announced = "rebelote_announced"
    Rebelote_Played = "rebelote_played"
    Lost = "lost"