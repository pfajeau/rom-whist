"""
This module implements galene service functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from romwhist.galene.client import (
    GaleneClient,
    GaleneConflict,
    GaleneError,
    GaleneUnavailable,
)
from romwhist.galene.config import GaleneConfig


# How long to stop calling Galene after a failure, so an unreachable server
# does not add a request timeout to every game page render.
UNAVAILABLE_COOLDOWN_SECONDS = 30


@dataclass
class VideoToken:
    name: str
    expires_at: datetime


@dataclass
class VideoRoom:
    game_type: str
    game_id: str
    group: str
    expires_at: datetime
    refresh_margin_seconds: int = 600
    tokens: dict = field(default_factory=dict)  # alias -> VideoToken

    def token_is_fresh(self, alias, now):
        token = self.tokens.get(alias)
        if token is None:
            return False
        return token.expires_at - timedelta(
            seconds=self.refresh_margin_seconds) > now


class GaleneService:
    """Owns the lifetime of the Galene group associated with each game.

    All video conferencing logic lives here: game specific route modules only
    call create_room, join_url, teardown and page_context.

    The room registry is in memory, matching how games themselves are kept in
    memory by the game modules. Room and group names are derived from the game
    type and game id, so a restarted process can still recognise and clean up
    rooms it did not create.
    """

    def __init__(self, config, client=None, expiration_hours=8, clock=None):
        self.config = config
        self.client = client or (GaleneClient(config) if config.enabled else None)
        self.expiration_hours = expiration_hours
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.rooms = {}
        self._lock = threading.RLock()
        self._unavailable_until = 0.0

    # -- availability --------------------------------------------------------

    @property
    def enabled(self):
        return bool(self.config.enabled and self.client is not None)

    def available(self):
        """True when Galene may be called right now."""
        if not self.enabled:
            return False
        return time.monotonic() >= self._unavailable_until

    def _mark_unavailable(self, exception):
        self._unavailable_until = time.monotonic() + UNAVAILABLE_COOLDOWN_SECONDS
        logging.warning("Galene is unavailable, pausing video operations: %s", exception)

    def _run(self, description, operation, *args, **kwargs):
        """Run a Galene operation, degrading to a logged failure."""
        if not self.available():
            return None
        try:
            return operation(*args, **kwargs)
        except GaleneUnavailable as exception:
            self._mark_unavailable(exception)
            return None
        except GaleneError as exception:
            logging.error("Galene %s failed: %s", description, exception)
            return None

    # -- room lifecycle ------------------------------------------------------

    def _new_expiry(self):
        hours = self.expiration_hours
        if self.config.token_ttl_seconds:
            hours = self.config.token_ttl_seconds / 3600.0
        return self.clock() + timedelta(hours=hours)

    def _refresh_margin_seconds(self):
        """Renew tokens shortly before they expire, never later than 10 min."""
        lifetime = self._new_expiry() - self.clock()
        return max(30, min(600, int(lifetime.total_seconds() / 10)))

    def get_room(self, game_type, game_id):
        with self._lock:
            return self.rooms.get((str(game_type), str(game_id)))

    def video_enabled(self, game_type, game_id):
        return self.get_room(game_type, game_id) is not None

    def create_room(self, game_type, game_id, max_players):
        """Create the Galene group for a game. Returns True on success.

        Failure is never fatal for the game: video is simply unavailable.
        """
        if not self.enabled:
            return False

        game_type, game_id = str(game_type), str(game_id)
        group = self.config.group_name(game_type, game_id)
        expires_at = self._new_expiry()

        created = self._run(
            "create group", self._create_group, group, max_players, expires_at)
        if created is None:
            return False

        with self._lock:
            self.rooms[(game_type, game_id)] = VideoRoom(
                game_type=game_type,
                game_id=game_id,
                group=group,
                expires_at=expires_at,
                refresh_margin_seconds=self._refresh_margin_seconds(),
            )
        logging.info("Galene room %s created for game %s/%s", group, game_type, game_id)
        return True

    def _create_group(self, group, max_players, expires_at):
        try:
            self.client.create_group(
                group,
                display_name="%s %s" % (self.config.group_prefix, group.rsplit("-", 1)[-1]),
                description="Video room for game %s" % group,
                max_clients=max_players + self.config.max_extra_clients,
                expires=expires_at,
            )
            return True
        except GaleneConflict:
            # A group with this name survived an earlier game that reused the
            # id. Purge its tokens (they would otherwise still authorise a
            # join to the new room) and replace the group.
            logging.info("Galene group %s already exists, replacing it", group)
            self._purge_group(group)
            self.client.create_group(
                group,
                display_name="%s %s" % (self.config.group_prefix, group.rsplit("-", 1)[-1]),
                description="Video room for game %s" % group,
                max_clients=max_players + self.config.max_extra_clients,
                expires=expires_at,
            )
            return True

    def _purge_group(self, group):
        """Delete every token of a group, then the group itself."""
        try:
            names = self.client.list_tokens(group)
        except GaleneError:
            names = []
        for name in names:
            try:
                self.client.delete_token(group, name)
            except GaleneError as exception:
                logging.warning("Could not delete Galene token %s: %s", name, exception)
        try:
            etag = self.client.get_group_etag(group)
            self.client.delete_group(group, etag)
        except GaleneError as exception:
            logging.warning("Could not delete Galene group %s: %s", group, exception)

    def teardown(self, game_type, game_id, asynchronous=True):
        """Remove the room and its Galene group when the game ends."""
        game_type, game_id = str(game_type), str(game_id)
        with self._lock:
            room = self.rooms.pop((game_type, game_id), None)
        group = room.group if room else self.config.group_name(game_type, game_id)

        if not self.enabled:
            return

        if asynchronous:
            thread = threading.Thread(
                target=self._run, args=("teardown %s" % group, self._purge_group, group),
                daemon=True)
            thread.start()
        else:
            self._run("teardown %s" % group, self._purge_group, group)

    def forget_room(self, game_type, game_id):
        """Drop the registry entry without calling Galene."""
        with self._lock:
            self.rooms.pop((str(game_type), str(game_id)), None)

    # -- joining -------------------------------------------------------------

    def join_url(self, game_type, game_id, alias):
        """Return a Galene URL that logs this player straight into the room."""
        room = self.get_room(game_type, game_id)
        if room is None or not self.enabled:
            return None

        with self._lock:
            if not room.token_is_fresh(alias, self.clock()):
                token = self._run("create token", self._create_token, room, alias)
                if token is None:
                    return None
                room.tokens[alias] = token

        token = room.tokens.get(alias)
        if token is None:
            return None
        return self.config.token_url(room.group, token.name)

    def _create_token(self, room, alias):
        name = self.client.create_token(
            room.group,
            username=alias,
            permissions=self.config.permissions,
            expires=room.expires_at,
        )
        return VideoToken(name=name, expires_at=room.expires_at)

    # -- view helper ---------------------------------------------------------

    def page_context(self, game_type, game_id, alias, is_owner):
        """Context values for a game page.

        The join URL is produced here so enabling video while a game is in
        progress is picked up by the next rendered page, without storing
        bearer URLs in the session cookie.
        """
        room = self.get_room(game_type, game_id)
        return {
            "video_enabled": room is not None,
            "video_available": self.enabled,
            "video_owner": bool(is_owner),
            "galene_url": self.join_url(game_type, game_id, alias) if room is not None else None,
        }

    def enable_video(self, game_type, game_id, max_players):
        """Create the room on demand, e.g. requested by the game owner."""
        if self.get_room(game_type, game_id) is not None:
            return True
        return self.create_room(game_type, game_id, max_players)

    def disable_video(self, game_type, game_id):
        self.teardown(game_type, game_id)

    # -- cleanup -------------------------------------------------------------

    def sweep(self, live_games):
        """Delete groups of games that no longer exist.

        live_games maps a game type to an iterable of game ids that are still
        running. Groups belonging to vanished games are purged from Galene,
        which also covers groups left behind by a previous process.
        """
        if not self.enabled or not self.available():
            return

        live = {
            str(game_type): {str(game_id) for game_id in game_ids}
            for game_type, game_ids in live_games.items()
        }

        with self._lock:
            stale = [
                (room.game_type, room.game_id)
                for room in self.rooms.values()
                if room.game_type in live
                and room.game_id not in live[room.game_type]
            ]
        for game_type, game_id in stale:
            self.forget_room(game_type, game_id)

        groups = self._run("list groups", self.client.list_groups)
        if groups is None:
            return

        # Sweeping is triggered per game type, so only groups of the game types
        # passed in are considered: rooms of other games must be left alone.
        prefix = self.config.group_prefix + "-"
        for group in groups:
            if not group.startswith(prefix):
                continue
            name = group[len(prefix):]
            for game_type, game_ids in live.items():
                marker = game_type + "-"
                if not name.startswith(marker):
                    continue
                if name[len(marker):] in game_ids:
                    break
                logging.info("Removing orphaned Galene group %s", group)
                self._run("sweep %s" % group, self._purge_group, group)
                break


_service = None
_service_lock = threading.Lock()


def configure(app):
    """Create the process wide service from the application configuration."""
    global _service
    with _service_lock:
        config = GaleneConfig.from_app(app)
        _service = GaleneService(
            config,
            expiration_hours=app.config.get("GAME_EXPIRATION_HOURS", 8))
        if config.enabled:
            logging.info("Galene video chat enabled for %s", config.api_url)
        else:
            logging.info("Galene video chat disabled")
        return _service


def get_service():
    """Return the configured service, creating a disabled one if needed."""
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = GaleneService(GaleneConfig())
    return _service
