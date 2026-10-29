"""
This module implements the provider neutral video service interface.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class VideoToken:
    """A per player credential that authorises joining one room."""

    name: str
    expires_at: datetime


@dataclass
class VideoRoom:
    """A video room associated with one game.

    ``name`` is the provider's identifier for the room. ``handle`` is a free
    form dict providers may use for extra state.
    """

    game_type: str
    game_id: str
    name: str
    expires_at: datetime
    refresh_margin_seconds: int = 600
    handle: dict = field(default_factory=dict)
    tokens: dict = field(default_factory=dict)  # alias -> VideoToken

    def token_is_fresh(self, alias, now):
        token = self.tokens.get(alias)
        if token is None:
            return False
        return token.expires_at - timedelta(
            seconds=self.refresh_margin_seconds) > now


class VideoService(ABC):
    """Everything the application needs from a video conferencing provider.

    Game specific route modules only use the methods below, so swapping the
    provider never touches gameplay code. Implementations must degrade to a
    logged failure instead of raising: video problems are never fatal.
    """

    #: True when a provider is configured and usable.
    @property
    @abstractmethod
    def enabled(self):
        raise NotImplementedError

    @abstractmethod
    def available(self):
        """True when the provider may be called right now."""

    @abstractmethod
    def create_room(self, game_type, game_id, max_players):
        """Create the room for a game. Returns True on success."""

    @abstractmethod
    def enable_video(self, game_type, game_id, max_players):
        """Create the room on demand, e.g. requested by the game owner."""

    @abstractmethod
    def disable_video(self, game_type, game_id):
        """Remove the room, e.g. requested by the game owner."""

    @abstractmethod
    def teardown(self, game_type, game_id, asynchronous=True):
        """Remove the room and its remote objects when the game ends."""

    @abstractmethod
    def forget_room(self, game_type, game_id):
        """Drop the registry entry without calling the provider."""

    @abstractmethod
    def room_exists(self, game_type, game_id):
        """True when a room is registered for this game."""

    @abstractmethod
    def join_url(self, game_type, game_id, alias):
        """Return a URL that logs this player straight into the room."""

    @abstractmethod
    def page_context(self, game_type, game_id, alias, is_owner):
        """Context values for the video button on a game page."""

    @abstractmethod
    def sweep(self, live_games):
        """Remove rooms whose game no longer exists."""

    @abstractmethod
    def start_sweeper(self, live_games_provider, interval_seconds=900):
        """Periodically purge rooms whose game no longer exists."""

    @abstractmethod
    def stop_sweeper(self):
        """Stop the periodic sweeper, if one is running."""
