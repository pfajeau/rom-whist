"""
This module implements the provider neutral video configuration.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

from dataclasses import dataclass

DEFAULT_PROVIDER = "none"


@dataclass(frozen=True)
class VideoConfig:
    """Which video provider to use and how the feature behaves.

    Provider specific settings (server URLs, credentials, permissions) are
    read by the provider itself; this object only carries what is common to
    every video service.
    """

    provider: str = DEFAULT_PROVIDER
    enabled: bool = False
    expiration_hours: float = 8
    sweep_enabled: bool = True
    sweep_interval_seconds: int = 900

    @classmethod
    def from_app(cls, app):
        """Build the configuration from the Flask application config.

        Only an explicit VIDEO_PROVIDER selects a provider; anything else keeps
        the feature completely inert.
        """
        provider = (app.config.get("VIDEO_PROVIDER") or DEFAULT_PROVIDER)
        provider = str(provider).strip().lower() or DEFAULT_PROVIDER
        enabled = bool(app.config.get(
            "VIDEO_ENABLED", provider != DEFAULT_PROVIDER))

        return cls(
            provider=provider,
            enabled=enabled and provider != DEFAULT_PROVIDER,
            expiration_hours=float(app.config.get("GAME_EXPIRATION_HOURS", 8)),
            sweep_enabled=bool(app.config.get("VIDEO_SWEEP_ENABLED", True)),
            sweep_interval_seconds=int(
                app.config.get("VIDEO_SWEEP_INTERVAL_SECONDS", 900)),
        )
