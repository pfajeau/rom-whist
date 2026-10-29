"""
This module implements the inert video service used when none is configured.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from romwhist.video.base import VideoService
from romwhist.video.config import VideoConfig


class NullVideoService(VideoService):
    """A video service that does nothing.

    It exists so the rest of the application never needs to check whether a
    provider is configured: every call is a harmless no-op.
    """

    def __init__(self, config=None):
        self.config = config or VideoConfig()

    @property
    def enabled(self):
        return False

    def available(self):
        return False

    def create_room(self, game_type, game_id, max_players):
        return False

    def enable_video(self, game_type, game_id, max_players):
        return False

    def disable_video(self, game_type, game_id):
        return None

    def teardown(self, game_type, game_id, asynchronous=True):
        return None

    def forget_room(self, game_type, game_id):
        return None

    def room_exists(self, game_type, game_id):
        return False

    def join_url(self, game_type, game_id, alias):
        return None

    def page_context(self, game_type, game_id, alias, is_owner):
        return {
            "video_enabled": False,
            "video_available": False,
            "video_owner": bool(is_owner),
            "video_join_url": None,
        }

    def sweep(self, live_games):
        return None

    def start_sweeper(self, live_games_provider, interval_seconds=900):
        return None

    def stop_sweeper(self):
        return None


def create_service(app_config, video_config=None, expiration_hours=None):
    """Build the inert service. Always succeeds: video is simply off."""
    return NullVideoService(video_config)
