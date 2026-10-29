"""
This module implements video package initialization.

The application only ever imports this package: the concrete video provider
(if any) is chosen by configuration and instantiated at run time.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from romwhist.video.base import VideoRoom, VideoService, VideoToken
from romwhist.video.config import VideoConfig
from romwhist.video.errors import VideoConflict, VideoError, VideoUnavailable
from romwhist.video.factory import (
    available_providers,
    configure,
    create_service,
    get_service,
    register_provider,
    reset_service,
    resolve_config,
)
from romwhist.video.null import NullVideoService

__all__ = [
    "NullVideoService",
    "VideoConfig",
    "VideoConflict",
    "VideoError",
    "VideoRoom",
    "VideoService",
    "VideoToken",
    "VideoUnavailable",
    "available_providers",
    "configure",
    "create_service",
    "get_service",
    "register_provider",
    "reset_service",
    "resolve_config",
]
