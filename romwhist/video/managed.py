"""
This module implements the provider neutral video room bookkeeping.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import logging
import threading
import time
from datetime import datetime, timedelta, timezone

from romwhist.video.base import VideoRoom, VideoService, VideoToken
from romwhist.video.errors import VideoConflict, VideoError, VideoUnavailable


# How long to stop calling a provider after a failure, so an unreachable
# server does not add a request timeout to every game page render.
UNAVAILABLE_COOLDOWN_SECONDS = 30


class ManagedVideoService(VideoService):
    """Bookkeeping shared by every video provider.

    Owns the lifetime of the room associated with each game: the in memory
    registry, the per player token cache, the unavailability cooldown and the
    sweeper that removes rooms whose game has vanished.

    The room registry is in memory, matching how games themselves are kept in
    memory by the game modules. Room names are derived from the game type and
    game id, so a restarted process can still recognise and clean up rooms it
    did not create.

    Subclasses implement the ``_remote_*`` primitives that talk to the actual
    conferencing service.
    """

    def __init__(self, config, expiration_hours=None, clock=None):
        # ``config`` carries the provider specific settings. ``expiration_hours``
        # defaults to the value of the provider neutral configuration.
        self.config = config
        self.expiration_hours = (
            getattr(config, "expiration_hours", None)
            if expiration_hours is None else expiration_hours)
        if self.expiration_hours is None:
            self.expiration_hours = 8
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        self.rooms = {}
        self._lock = threading.RLock()
        self._unavailable_until = 0.0
        self._sweeper = None
        self._stop_sweeper = threading.Event()

    # -- provider primitives, implemented by subclasses ----------------------

    def _remote_create(self, room):
        """Create the remote room. Raise VideoConflict when it exists."""
        raise NotImplementedError

    def _remote_destroy(self, room):
        """Delete the remote room and any credential attached to it."""
        raise NotImplementedError

    def _remote_join_url(self, room, alias, token):
        """Build the URL that logs ``alias`` into ``room`` with ``token``."""
        raise NotImplementedError

    def _remote_mint_token(self, room, alias):
        """Ask the provider for a new credential. Return its name."""
        raise NotImplementedError

    def _remote_list_rooms(self):
        """Return the names of every room the provider knows about."""
        raise NotImplementedError

    def room_name(self, game_type, game_id):
        """Provider name of the room of a game."""
        raise NotImplementedError

    # -- availability --------------------------------------------------------

    @property
    def enabled(self):
        return bool(getattr(self.config, "enabled", False))

    def available(self):
        """True when the provider may be called right now."""
        if not self.enabled:
            return False
        return time.monotonic() >= self._unavailable_until

    def _mark_unavailable(self, exception):
        self._unavailable_until = time.monotonic() + UNAVAILABLE_COOLDOWN_SECONDS
        logging.warning(
            "Video provider is unavailable, pausing video operations: %s",
            exception)

    def _run(self, description, operation, *args, **kwargs):
        """Run a provider operation, degrading to a logged failure."""
        if not self.available():
            return None
        try:
            return operation(*args, **kwargs)
        except VideoUnavailable as exception:
            self._mark_unavailable(exception)
            return None
        except VideoError as exception:
            logging.error("Video %s failed: %s", description, exception)
            return None

    # -- room lifecycle ------------------------------------------------------

    def _lifetime_hours(self):
        """How long a freshly created room and its tokens stay valid."""
        return self.expiration_hours

    def _new_expiry(self):
        return self.clock() + timedelta(hours=self._lifetime_hours())

    def _refresh_margin_seconds(self):
        """Renew tokens shortly before they expire, never later than 10 min."""
        lifetime = self._new_expiry() - self.clock()
        return max(30, min(600, int(lifetime.total_seconds() / 10)))

    def get_room(self, game_type, game_id):
        with self._lock:
            return self.rooms.get((str(game_type), str(game_id)))

    def room_exists(self, game_type, game_id):
        return self.get_room(game_type, game_id) is not None

    def create_room(self, game_type, game_id, max_players):
        """Create the room for a game. Returns True on success.

        Failure is never fatal for the game: video is simply unavailable.
        """
        if not self.enabled:
            return False

        game_type, game_id = str(game_type), str(game_id)
        room = VideoRoom(
            game_type=game_type,
            game_id=game_id,
            name=self.room_name(game_type, game_id),
            expires_at=self._new_expiry(),
            refresh_margin_seconds=self._refresh_margin_seconds(),
            handle={"max_players": max_players},
        )

        created = self._run("create room", self._create_remote, room)
        if created is None:
            return False

        with self._lock:
            self.rooms[(game_type, game_id)] = room
        logging.info(
            "Video room %s created for game %s/%s",
            room.name, game_type, game_id)
        return True

    def _create_remote(self, room):
        try:
            self._remote_create(room)
            return True
        except VideoConflict:
            # A room with this name survived an earlier game that reused the
            # id. Purge its credentials (they would otherwise still authorise
            # a join to the new room) and replace the room.
            logging.info("Video room %s already exists, replacing it", room.name)
            self._remote_destroy(room)
            self._remote_create(room)
            return True

    def teardown(self, game_type, game_id, asynchronous=True):
        """Remove the room and its remote object when the game ends."""
        game_type, game_id = str(game_type), str(game_id)
        with self._lock:
            room = self.rooms.pop((game_type, game_id), None)
        if room is None:
            room = VideoRoom(
                game_type=game_type,
                game_id=game_id,
                name=self.room_name(game_type, game_id),
                expires_at=self._new_expiry(),
            )

        if not self.enabled:
            return

        if asynchronous:
            thread = threading.Thread(
                target=self._run,
                args=("teardown %s" % room.name, self._remote_destroy, room),
                daemon=True)
            thread.start()
        else:
            self._run("teardown %s" % room.name, self._remote_destroy, room)

    def forget_room(self, game_type, game_id):
        """Drop the registry entry without calling the provider."""
        with self._lock:
            self.rooms.pop((str(game_type), str(game_id)), None)

    # -- joining -------------------------------------------------------------

    def join_url(self, game_type, game_id, alias):
        """Return a URL that logs this player straight into the room."""
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
        return self._remote_join_url(room, alias, token)

    def _create_token(self, room, alias):
        name = self._remote_mint_token(room, alias)
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
            "video_join_url": (
                self.join_url(game_type, game_id, alias)
                if room is not None else None),
        }

    def enable_video(self, game_type, game_id, max_players):
        """Create the room on demand, e.g. requested by the game owner."""
        if self.get_room(game_type, game_id) is not None:
            return True
        return self.create_room(game_type, game_id, max_players)

    def disable_video(self, game_type, game_id):
        """Disable video for a game. Called from a user action, so it waits."""
        self.teardown(game_type, game_id, asynchronous=False)

    # -- cleanup -------------------------------------------------------------

    def sweep(self, live_games):
        """Delete rooms of games that no longer exist.

        live_games maps a game type to an iterable of game ids that are still
        running. Rooms belonging to vanished games are purged from the
        provider, which also covers rooms left behind by a previous process.
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

        names = self._run("list rooms", self._remote_list_rooms)
        if names is None:
            return

        # Sweeping is triggered per game type, so only rooms of the game types
        # passed in are considered: rooms of other games must be left alone.
        for name, game_type, game_id in self._parse_names(names, live):
            if game_id in live[game_type]:
                continue
            logging.info("Removing orphaned video room %s", name)
            self._run(
                "sweep %s" % name, self._remote_destroy,
                VideoRoom(game_type=game_type, game_id=game_id, name=name,
                          expires_at=self._new_expiry()))

    def _parse_names(self, names, live):
        """Yield (name, game_type, game_id) for names belonging to a live type.

        Providers whose names cannot be parsed simply yield nothing, so the
        sweep is a no-op rather than deleting the wrong room.
        """
        return []

    def start_sweeper(self, live_games_provider, interval_seconds=900):
        """Periodically purge rooms whose game no longer exists.

        Live games are only known to the game modules, so the provider
        callable supplies them. The first sweep happens immediately: after a
        restart no games exist, so any leftover room is an orphan.
        """
        if not self.enabled or self._sweeper is not None:
            return self._sweeper

        self._stop_sweeper.clear()
        self._sweeper = threading.Thread(
            target=self._sweeper_loop,
            args=(live_games_provider, interval_seconds),
            name="video-sweeper",
            daemon=True)
        self._sweeper.start()
        logging.info("Video sweeper started, interval %s seconds",
                     interval_seconds)
        return self._sweeper

    def stop_sweeper(self):
        self._stop_sweeper.set()
        sweeper = self._sweeper
        self._sweeper = None
        if sweeper is not None and sweeper is not threading.current_thread():
            sweeper.join(timeout=5)

    def _sweeper_loop(self, live_games_provider, interval_seconds):
        while True:
            try:
                self.sweep(live_games_provider())
            except Exception:
                logging.exception("Video sweep failed")
            if self._stop_sweeper.wait(interval_seconds):
                return
