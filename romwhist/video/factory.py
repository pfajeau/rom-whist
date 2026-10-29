"""
This module implements the video provider registry and factory.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import importlib
import logging
import threading

from romwhist.video.config import VideoConfig
from romwhist.video.null import NullVideoService

# Provider name -> "module:callable" creating the service. Entries are
# resolved lazily, so a provider is only imported when it is selected: the
# application has no static dependency on any implementation.
_PROVIDERS = {
    "none": "romwhist.video.null:create_service",
    "galene": "romwhist.video.galene:create_service",
}

_service = None
_service_lock = threading.Lock()


def register_provider(name, target):
    """Register a provider factory as ``"module:callable"``.

    The callable receives ``(app_config, video_config, expiration_hours)`` and
    returns a ``VideoService``. Providers may also be registered to replace a
    built in one, which is handy in tests.
    """
    _PROVIDERS[str(name).strip().lower()] = target


def available_providers():
    return sorted(_PROVIDERS)


def _load(target):
    module_name, _, attribute = target.partition(":")
    module = importlib.import_module(module_name)
    return getattr(module, attribute)


def _apply_legacy_settings(app, video_config):
    """Upgrade pre-abstraction settings that did not name a provider.

    Installations created before the video abstraction only had
    ``GALENE_ENABLED`` and ``GALENE_SWEEP_*``. Rather than break them, those
    settings are still honoured when the new ones are absent. This lives here,
    in the module that already maps provider names to modules, so the rest of
    the application stays provider agnostic.
    """
    provider = video_config.provider
    enabled = video_config.enabled
    sweep_enabled = video_config.sweep_enabled
    sweep_interval = video_config.sweep_interval_seconds

    if "VIDEO_PROVIDER" not in app.config and "VIDEO_ENABLED" not in app.config:
        # A pre-abstraction installation only has GALENE_ENABLED, so it is
        # treated as the provider selection and master switch at once.
        logging.warning(
            "GALENE_ENABLED is deprecated; set VIDEO_PROVIDER = 'galene' and "
            "VIDEO_ENABLED instead")
        provider = "galene" if app.config.get("GALENE_ENABLED") else "none"
        enabled = provider != "none"

    # Sweeper settings predate the abstraction under a provider specific name.
    if "VIDEO_SWEEP_ENABLED" not in app.config:
        sweep_enabled = bool(app.config.get("GALENE_SWEEP_ENABLED", sweep_enabled))
    if "VIDEO_SWEEP_INTERVAL_SECONDS" not in app.config:
        sweep_interval = int(app.config.get(
            "GALENE_SWEEP_INTERVAL_SECONDS", sweep_interval))

    if (provider, enabled, sweep_enabled, sweep_interval) == (
            video_config.provider, video_config.enabled,
            video_config.sweep_enabled, video_config.sweep_interval_seconds):
        return video_config

    return VideoConfig(
        provider=provider,
        enabled=enabled and provider not in ("", "none"),
        expiration_hours=video_config.expiration_hours,
        sweep_enabled=sweep_enabled,
        sweep_interval_seconds=sweep_interval,
    )


def resolve_config(app, video_config=None):
    """Return the effective configuration, applying legacy settings."""
    return _apply_legacy_settings(
        app, video_config or VideoConfig.from_app(app))


def create_service(app, video_config=None):
    """Build the service for the provider selected in the configuration."""
    video_config = resolve_config(app, video_config)

    name = video_config.provider
    if not video_config.enabled or name in ("", "none"):
        return _load(_PROVIDERS["none"])(app.config, video_config)

    target = _PROVIDERS.get(name)
    if target is None:
        logging.error(
            "Unknown video provider %r; video chat is disabled. Known "
            "providers: %s", name, ", ".join(available_providers()))
        return _load(_PROVIDERS["none"])(app.config, video_config)

    try:
        service = _load(target)(
            app.config, video_config, video_config.expiration_hours)
    except (ImportError, AttributeError):
        logging.exception(
            "Video provider %r could not be loaded; video chat is disabled",
            name)
        return _load(_PROVIDERS["none"])(app.config, video_config)

    if service.enabled:
        logging.info("Video chat enabled with provider %s", name)
    else:
        logging.info("Video chat provider %s is not configured", name)
    return service


def configure(app, live_games_provider=None):
    """Create the process wide service from the application configuration.

    ``live_games_provider`` is a callable returning the game ids per game type
    that are still running. It is only used by the periodic sweeper, and is
    injected rather than imported so this module never depends on the game
    modules.
    """
    global _service
    with _service_lock:
        video_config = resolve_config(app)
        _service = create_service(app, video_config)
        if live_games_provider is not None and video_config.sweep_enabled:
            _service.start_sweeper(
                live_games_provider,
                interval_seconds=video_config.sweep_interval_seconds)
    return _service


def get_service():
    """Return the configured service, creating an inert one if needed."""
    global _service
    if _service is None:
        with _service_lock:
            if _service is None:
                _service = NullVideoService()
    return _service


def reset_service():
    """Forget the process wide service. Intended for tests."""
    global _service
    with _service_lock:
        if _service is not None:
            _service.stop_sweeper()
        _service = None
