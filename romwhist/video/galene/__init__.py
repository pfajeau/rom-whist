"""
This module implements the Galene video provider package.

The application never imports this package directly: the video factory only
loads it when VIDEO_PROVIDER selects "galene".

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from romwhist.video.galene.config import GaleneConfig
from romwhist.video.galene.service import GaleneService, create_service

__all__ = ["GaleneConfig", "GaleneService", "create_service"]
