"""
This module implements galene configuration functionality.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import logging
from dataclasses import dataclass


@dataclass(frozen=True)
class GaleneConfig:
    """Configuration needed to talk to a Galene server.

    A disabled configuration makes every Galene operation a no-op, so the
    video feature stays completely inert unless it is explicitly enabled.
    """

    enabled: bool = False
    api_url: str = ""
    public_url: str = ""
    admin_user: str = ""
    admin_password: str = ""
    group_prefix: str = "cards"
    permissions: tuple = ("present", "message")
    verify_tls: bool = True
    timeout: float = 3.0
    max_extra_clients: int = 1
    token_ttl_seconds: int = 0

    @property
    def api_base(self):
        return self.api_url.rstrip("/") + "/galene-api/v0"

    def group_name(self, game_type, game_id):
        return "%s-%s-%s" % (self.group_prefix, game_type, game_id)

    def group_url(self, group):
        return "%s/group/%s/" % (self.public_url.rstrip("/"), group)

    def token_url(self, group, token):
        return "%s?token=%s" % (self.group_url(group), token)

    @classmethod
    def from_app(cls, app):
        """Build the configuration from the Flask application config.

        Galene is only active when it was selected as the video provider and
        GALENE_ENABLED is on. Missing required values are reported once and
        downgrade the configuration to disabled rather than raising during
        application startup.
        """
        if not app.config.get("GALENE_ENABLED", False):
            return cls()

        api_url = (app.config.get("GALENE_API_URL") or "").strip()
        public_url = (app.config.get("GALENE_PUBLIC_URL") or api_url).strip()
        admin_user = app.config.get("GALENE_ADMIN_USER") or ""
        admin_password = app.config.get("GALENE_ADMIN_PASSWORD") or ""

        missing = [
            name for name, value in (
                ("GALENE_API_URL", api_url),
                ("GALENE_PUBLIC_URL", public_url),
                ("GALENE_ADMIN_USER", admin_user),
                ("GALENE_ADMIN_PASSWORD", admin_password),
            ) if not value
        ]
        if missing:
            logging.error(
                "Galene video is enabled but %s is not set; video chat is disabled",
                ", ".join(missing))
            return cls()

        permissions = app.config.get("GALENE_PERMISSIONS") or ("present", "message")
        return cls(
            enabled=True,
            api_url=api_url,
            public_url=public_url,
            admin_user=admin_user,
            admin_password=admin_password,
            group_prefix=app.config.get("GALENE_GROUP_PREFIX") or "cards",
            permissions=tuple(permissions),
            verify_tls=bool(app.config.get("GALENE_VERIFY_TLS", True)),
            timeout=float(app.config.get("GALENE_TIMEOUT_SECONDS", 3.0)),
            max_extra_clients=int(app.config.get("GALENE_MAX_EXTRA_CLIENTS", 1)),
            token_ttl_seconds=int(app.config.get("GALENE_TOKEN_TTL_HOURS", 0) or 0) * 3600,
        )
