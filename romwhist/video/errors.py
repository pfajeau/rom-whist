"""
This module implements the provider neutral video error hierarchy.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""


class VideoError(Exception):
    """Base class for video provider errors."""


class VideoUnavailable(VideoError):
    """The video service cannot be reached or answered unexpectedly.

    Callers treat this as "video is not available right now" and never let it
    break gameplay.
    """


class VideoConflict(VideoError):
    """A precondition failed: the object exists or changed concurrently."""
