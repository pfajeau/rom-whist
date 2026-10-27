"""
This module implements galene package initialization.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from romwhist.galene.config import GaleneConfig
from romwhist.galene.service import GaleneService, configure, get_service

__all__ = ["GaleneConfig", "GaleneService", "configure", "get_service"]
