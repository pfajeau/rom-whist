"""
This module implements the Galene video provider.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import logging

from romwhist.video.errors import VideoError
from romwhist.video.managed import UNAVAILABLE_COOLDOWN_SECONDS, ManagedVideoService
from romwhist.video.galene.client import GaleneClient
from romwhist.video.galene.config import GaleneConfig

__all__ = [
    "GaleneService",
    "UNAVAILABLE_COOLDOWN_SECONDS",
    "create_service",
]


class GaleneService(ManagedVideoService):
    """Galene implementation of the video service.

    Galene stores rooms as *groups*; joining a group requires a stateful token
    bound to the player's alias. Everything generic (registry, token cache,
    cooldown, sweeper) is inherited from ManagedVideoService.
    """

    def __init__(self, config, client=None, expiration_hours=8, clock=None):
        super().__init__(config, expiration_hours=expiration_hours, clock=clock)
        self.client = client or (GaleneClient(config) if config.enabled else None)

    @property
    def enabled(self):
        return bool(self.config.enabled and self.client is not None)

    # -- provider primitives -------------------------------------------------

    def _lifetime_hours(self):
        if self.config.token_ttl_seconds:
            return self.config.token_ttl_seconds / 3600.0
        return self.expiration_hours

    def room_name(self, game_type, game_id):
        return self.config.group_name(game_type, game_id)

    def _display_name(self, room):
        suffix = room.name.rsplit("-", 1)[-1]
        return "%s %s" % (self.config.group_prefix, suffix)

    def _remote_create(self, room):
        self.client.create_group(
            room.name,
            display_name=self._display_name(room),
            description="Video room for game %s" % room.name,
            max_clients=room.handle["max_players"] + self.config.max_extra_clients,
            expires=room.expires_at,
        )

    def _remote_destroy(self, room):
        """Delete every token of a group, then the group itself."""
        try:
            names = self.client.list_tokens(room.name)
        except VideoError:
            names = []
        for name in names:
            try:
                self.client.delete_token(room.name, name)
            except VideoError as exception:
                logging.warning(
                    "Could not delete Galene token %s: %s", name, exception)
        try:
            etag = self.client.get_group_etag(room.name)
            self.client.delete_group(room.name, etag)
        except VideoError as exception:
            logging.warning(
                "Could not delete Galene group %s: %s", room.name, exception)

    def _remote_mint_token(self, room, alias):
        return self.client.create_token(
            room.name,
            username=alias,
            permissions=self.config.permissions,
            expires=room.expires_at,
        )

    def _remote_join_url(self, room, alias, token):
        return self.config.token_url(room.name, token.name)

    def _remote_list_rooms(self):
        return self.client.list_groups()

    def _parse_names(self, names, live):
        """Match ``<prefix>-<game type>-<game id>`` names to the game types."""
        prefix = self.config.group_prefix + "-"
        for name in names:
            if not name.startswith(prefix):
                continue
            rest = name[len(prefix):]
            for game_type in live:
                marker = game_type + "-"
                if not rest.startswith(marker):
                    continue
                yield name, game_type, rest[len(marker):]
                break


class _AppConfig:
    """Expose the raw Flask config mapping to GaleneConfig.from_app()."""

    def __init__(self, config):
        self.config = config or {}


def create_service(app_config, video_config, expiration_hours=8):
    """Build a Galene service from the application configuration.

    The provider-neutral switch decides whether video is on; Galene specific
    settings are then read, and missing ones disable the feature rather than
    raising during application startup.
    """
    config = dict(app_config or {})
    config["GALENE_ENABLED"] = video_config.enabled
    galene_config = GaleneConfig.from_app(_AppConfig(config))
    if not galene_config.enabled:
        logging.info("Galene video chat disabled")
    return GaleneService(galene_config, expiration_hours=expiration_hours)
