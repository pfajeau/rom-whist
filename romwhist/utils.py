"""
This module implements utils functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import copy
import time

def get_timestamp():
    return time.time()

def copy_dict(dict1):
    dict2 = dict()
    for key in dict1.keys():
        dict2[key] = copy.copy(dict1[key])

    return dict2
