"""
This module implements the provider neutral video abstraction tests.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import os
import pathlib
import re
import unittest
from unittest.mock import MagicMock

from romwhist import video
from romwhist.video.base import VideoService
from romwhist.video.config import VideoConfig
from romwhist.video.null import NullVideoService

PACKAGE_ROOT = pathlib.Path(__file__).resolve().parent.parent / "romwhist"


class VideoConfigTests(unittest.TestCase):
    def _app(self, **config):
        app = MagicMock()
        app.config = config
        return app

    def test_absent_settings_mean_no_provider(self):
        config = VideoConfig.from_app(self._app())
        self.assertEqual(config.provider, "none")
        self.assertFalse(config.enabled)

    def test_provider_selects_the_implementation(self):
        config = VideoConfig.from_app(
            self._app(VIDEO_PROVIDER="galene"))
        self.assertEqual(config.provider, "galene")
        self.assertTrue(config.enabled)

    def test_master_switch_overrides_provider(self):
        config = VideoConfig.from_app(
            self._app(VIDEO_PROVIDER="galene", VIDEO_ENABLED=False))
        self.assertFalse(config.enabled)

    def test_explicit_none_is_never_enabled(self):
        config = VideoConfig.from_app(
            self._app(VIDEO_PROVIDER="none", VIDEO_ENABLED=True))
        self.assertFalse(config.enabled)

    def test_legacy_setting_still_selects_galene(self):
        app = self._app(
            GALENE_ENABLED=True,
            GALENE_API_URL="https://meet.example.org",
            GALENE_ADMIN_USER="admin",
            GALENE_ADMIN_PASSWORD="secret",
        )
        with self.assertLogs(level="WARNING"):
            service = video.create_service(app)
        from romwhist.video.galene.service import GaleneService
        self.assertIsInstance(service, GaleneService)
        self.assertTrue(service.enabled)

    def test_legacy_setting_off_keeps_video_off(self):
        app = self._app(GALENE_ENABLED=False)
        with self.assertLogs(level="WARNING"):
            service = video.create_service(app)
        self.assertIsInstance(service, NullVideoService)

    def test_legacy_sweep_settings_are_honoured(self):
        config = video.resolve_config(self._app(
            GALENE_ENABLED=True,
            GALENE_SWEEP_ENABLED=False,
            GALENE_SWEEP_INTERVAL_SECONDS=42,
        ))
        self.assertFalse(config.sweep_enabled)
        self.assertEqual(config.sweep_interval_seconds, 42)

    def test_new_sweep_settings_win_over_legacy_ones(self):
        config = video.resolve_config(self._app(
            VIDEO_PROVIDER="galene",
            VIDEO_SWEEP_ENABLED=True,
            VIDEO_SWEEP_INTERVAL_SECONDS=60,
            GALENE_SWEEP_ENABLED=False,
            GALENE_SWEEP_INTERVAL_SECONDS=42,
        ))
        self.assertTrue(config.sweep_enabled)
        self.assertEqual(config.sweep_interval_seconds, 60)

    def test_sweeper_settings_are_read(self):
        config = VideoConfig.from_app(self._app(
            VIDEO_PROVIDER="galene", VIDEO_SWEEP_ENABLED=False,
            VIDEO_SWEEP_INTERVAL_SECONDS=60, GAME_EXPIRATION_HOURS=3))
        self.assertFalse(config.sweep_enabled)
        self.assertEqual(config.sweep_interval_seconds, 60)
        self.assertEqual(config.expiration_hours, 3)


class NullVideoServiceTests(unittest.TestCase):
    def setUp(self):
        self.service = NullVideoService()

    def test_every_operation_is_inert(self):
        self.assertFalse(self.service.enabled)
        self.assertFalse(self.service.available())
        self.assertFalse(self.service.create_room("whist", "42", 6))
        self.assertFalse(self.service.enable_video("whist", "42", 6))
        self.assertFalse(self.service.room_exists("whist", "42"))
        self.assertIsNone(self.service.join_url("whist", "42", "alice"))
        self.assertIsNone(self.service.teardown("whist", "42"))
        self.assertIsNone(self.service.disable_video("whist", "42"))
        self.assertIsNone(self.service.sweep({"whist": ["42"]}))

    def test_page_context_has_the_documented_keys(self):
        context = self.service.page_context("whist", "42", "alice", True)
        self.assertEqual(
            set(context),
            {"video_enabled", "video_available", "video_owner",
             "video_join_url"})
        self.assertFalse(context["video_enabled"])
        self.assertIsNone(context["video_join_url"])
        self.assertTrue(context["video_owner"])

    def test_it_satisfies_the_service_interface(self):
        self.assertIsInstance(self.service, VideoService)


class VideoFactoryTests(unittest.TestCase):
    def _app(self, **config):
        app = MagicMock()
        app.config = config
        return app

    def test_no_provider_yields_the_null_service(self):
        service = video.create_service(self._app())
        self.assertIsInstance(service, NullVideoService)

    def test_unknown_provider_falls_back_to_null(self):
        with self.assertLogs(level="ERROR") as logs:
            service = video.create_service(
                self._app(VIDEO_PROVIDER="does-not-exist"))
        self.assertIsInstance(service, NullVideoService)
        self.assertIn("does-not-exist", "\n".join(logs.output))

    def test_galene_is_selected_by_configuration(self):
        service = video.create_service(self._app(
            VIDEO_PROVIDER="galene",
            GALENE_ENABLED=True,
            GALENE_API_URL="https://meet.example.org",
            GALENE_ADMIN_USER="admin",
            GALENE_ADMIN_PASSWORD="secret",
        ))
        from romwhist.video.galene.service import GaleneService
        self.assertIsInstance(service, GaleneService)
        self.assertTrue(service.enabled)

    def test_custom_provider_can_be_registered(self):
        created = []

        def factory(app_config, video_config, expiration_hours):
            service = NullVideoService(video_config)
            created.append(service)
            return service

        video.register_provider("test-fake", "romwhist.video.null:create_fake")
        # Registering a target that does not exist must not break the app:
        # the factory reports it and keeps video disabled.
        with self.assertLogs(level="ERROR"):
            service = video.create_service(self._app(VIDEO_PROVIDER="test-fake"))
        self.assertIsInstance(service, NullVideoService)
        self.assertEqual(created, [])
        video.register_provider(
            "none", "romwhist.video.null:create_service")

    def test_registered_provider_is_used(self):
        video.register_provider("test-fake", "tests.test_video:_fake_provider")
        try:
            service = video.create_service(self._app(VIDEO_PROVIDER="test-fake"))
            self.assertIsInstance(service, NullVideoService)
            self.assertIn("test-fake", service.config.provider)
        finally:
            video.register_provider("none", "romwhist.video.null:create_service")

    def test_get_service_is_inert_before_configuration(self):
        video.reset_service()
        try:
            self.assertIsInstance(video.get_service(), NullVideoService)
        finally:
            video.reset_service()


class NoGaleneDependencyTests(unittest.TestCase):
    """The application must not depend on any concrete video provider."""

    ALLOWED = PACKAGE_ROOT / "video" / "galene"

    def _python_files(self):
        for path in PACKAGE_ROOT.rglob("*.py"):
            if self.ALLOWED in path.parents:
                continue
            yield path

    def test_no_module_outside_the_provider_mentions_galene(self):
        offenders = []
        for path in self._python_files():
            if path == PACKAGE_ROOT / "video" / "factory.py":
                continue  # holds the provider -> module mapping
            text = path.read_text(encoding="utf-8")
            if re.search(r"\bgalene\b", text, re.I):
                offenders.append(str(path.relative_to(PACKAGE_ROOT)))
        self.assertEqual(
            offenders, [],
            "video provider leakage outside romwhist/video/galene: %s"
            % ", ".join(offenders))

    def test_no_module_imports_a_concrete_provider(self):
        offenders = []
        pattern = re.compile(r"^\s*(?:from|import)\s+romwhist\.video\.galene",
                             re.M)
        for path in self._python_files():
            if path == PACKAGE_ROOT / "video" / "factory.py":
                continue
            if pattern.search(path.read_text(encoding="utf-8")):
                offenders.append(str(path.relative_to(PACKAGE_ROOT)))
        self.assertEqual(offenders, [])

    def test_application_startup_works_without_any_provider(self):
        """Selecting no provider must leave the app fully functional."""
        from romwhist import video as video_module
        self.assertIn("none", video_module.available_providers())

    def test_templates_and_javascript_are_provider_neutral(self):
        offenders = []
        for folder in ("ui/templates", "ui/static/js"):
            for path in (PACKAGE_ROOT / folder).rglob("*"):
                if path.suffix not in (".html", ".js") or not path.is_file():
                    continue
                text = path.read_text(encoding="utf-8", errors="replace")
                if re.search(r"galene", text, re.I):
                    offenders.append(str(path.relative_to(PACKAGE_ROOT)))
        self.assertEqual(offenders, [], ", ".join(offenders))


def _fake_provider(app_config, video_config, expiration_hours):
    return NullVideoService(VideoConfig(
        provider="test-fake",
        enabled=True,
        expiration_hours=expiration_hours,
        sweep_enabled=video_config.sweep_enabled,
        sweep_interval_seconds=video_config.sweep_interval_seconds,
    ))


if __name__ == "__main__":
    unittest.main()
