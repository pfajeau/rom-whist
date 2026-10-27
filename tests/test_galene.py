"""
This module implements galene integration tests.

License: GNU General Public License (GPL) v3.0 or later.
This program is free software: you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option) any later version.

Author: Philippe Fajeau
"""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import requests

from romwhist import app as flask_app
from romwhist import galene as video
from romwhist.galene.client import (
    GaleneClient,
    GaleneConflict,
    GaleneUnavailable,
)
from romwhist.galene.config import GaleneConfig
from romwhist.galene.service import UNAVAILABLE_COOLDOWN_SECONDS, GaleneService
from romwhist.ohell import ohell_routes

_BOOTSTRAP_READY = False


def ensure_bootstrap(app):
    """create_app() installs Flask-Bootstrap; do the same once for route tests."""
    global _BOOTSTRAP_READY
    if _BOOTSTRAP_READY:
        return
    from flask_bootstrap import Bootstrap
    if not app.blueprints:
        Bootstrap(app)
    _BOOTSTRAP_READY = True

NOW = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


def make_config(**overrides):
    values = dict(
        enabled=True,
        api_url="https://galene.example.org",
        public_url="https://galene.example.org",
        admin_user="admin",
        admin_password="secret",
        group_prefix="cards",
        permissions=("present", "message"),
        verify_tls=True,
        timeout=3.0,
        max_extra_clients=1,
        token_ttl_seconds=0,
    )
    values.update(overrides)
    return GaleneConfig(**values)


NO_JSON = object()


def make_response(status=200, json_body=NO_JSON, headers=None):
    response = MagicMock()
    response.status_code = status
    response.headers = headers or {}
    response.text = ""
    if json_body is NO_JSON:
        response.json.side_effect = ValueError("no json")
    else:
        response.json.return_value = json_body
    return response


class GaleneConfigTests(unittest.TestCase):
    def test_disabled_by_default(self):
        app = MagicMock()
        app.config = {"GALENE_ENABLED": False}
        self.assertFalse(GaleneConfig.from_app(app).enabled)

    def test_ignores_settings_when_disabled(self):
        app = MagicMock()
        app.config = {"GALENE_ENABLED": False, "GALENE_API_URL": "https://x"}
        self.assertFalse(GaleneConfig.from_app(app).enabled)

    def test_missing_credentials_disable_feature(self):
        app = MagicMock()
        app.config = {
            "GALENE_ENABLED": True,
            "GALENE_API_URL": "https://galene.example.org",
            "GALENE_ADMIN_USER": "admin",
            "GALENE_ADMIN_PASSWORD": "",
        }
        self.assertFalse(GaleneConfig.from_app(app).enabled)

    def test_full_configuration_enables_feature(self):
        app = MagicMock()
        app.config = {
            "GALENE_ENABLED": True,
            "GALENE_API_URL": "https://galene.example.org/",
            "GALENE_ADMIN_USER": "admin",
            "GALENE_ADMIN_PASSWORD": "secret",
            "GALENE_TOKEN_TTL_HOURS": 2,
            "GAME_EXPIRATION_HOURS": 8,
        }
        config = GaleneConfig.from_app(app)
        self.assertTrue(config.enabled)
        self.assertEqual(config.token_ttl_seconds, 7200)
        self.assertEqual(
            config.api_base, "https://galene.example.org/galene-api/v0")

    def test_public_url_defaults_to_api_url(self):
        app = MagicMock()
        app.config = {
            "GALENE_ENABLED": True,
            "GALENE_API_URL": "https://internal:8443",
            "GALENE_ADMIN_USER": "admin",
            "GALENE_ADMIN_PASSWORD": "secret",
        }
        config = GaleneConfig.from_app(app)
        self.assertEqual(config.public_url, "https://internal:8443")

    def test_group_and_token_urls(self):
        config = make_config(public_url="https://meet.example.org/")
        group = config.group_name("whist", "42")
        self.assertEqual(group, "cards-whist-42")
        self.assertEqual(
            config.group_url(group),
            "https://meet.example.org/group/cards-whist-42/")
        self.assertEqual(
            config.token_url(group, "abc"),
            "https://meet.example.org/group/cards-whist-42/?token=abc")


class GaleneClientTests(unittest.TestCase):
    def setUp(self):
        self.session = MagicMock()
        self.client = GaleneClient(make_config(), session=self.session)

    def test_create_group_uses_if_none_match(self):
        self.session.request.return_value = make_response(201)
        self.client.create_group(
            "cards-whist-42", display_name="Whist 42",
            max_clients=7, expires=NOW + timedelta(hours=8))

        _, kwargs = self.session.request.call_args
        self.assertEqual(kwargs["headers"]["If-None-Match"], "*")
        self.assertEqual(kwargs["json"]["max-clients"], 7)
        self.assertEqual(kwargs["json"]["expires"], "2026-01-01T20:00:00Z")

    def test_create_group_conflict(self):
        self.session.request.return_value = make_response(412)
        with self.assertRaises(GaleneConflict):
            self.client.create_group("cards-whist-42")

    def test_delete_group_sends_etag(self):
        self.session.request.return_value = make_response(204)
        self.client.delete_group("cards-whist-42", '"123-456"')
        _, kwargs = self.session.request.call_args
        self.assertEqual(kwargs["headers"]["If-Match"], '"123-456"')

    def test_delete_group_tolerates_missing_group(self):
        self.session.request.return_value = make_response(404)
        self.client.delete_group("cards-whist-42", "")

    def test_create_token_returns_location(self):
        self.session.request.return_value = make_response(
            201, headers={"Location": "generated-token"})
        token = self.client.create_token(
            "cards-whist-42", username="alice",
            permissions=["present", "message"], expires=NOW)
        self.assertEqual(token, "generated-token")

        args, kwargs = self.session.request.call_args
        self.assertEqual(args[0], "POST")
        self.assertTrue(args[1].endswith("/.tokens/"))
        self.assertEqual(kwargs["json"]["username"], "alice")
        self.assertEqual(kwargs["json"]["permissions"], ["present", "message"])

    def test_create_token_without_location_fails(self):
        self.session.request.return_value = make_response(201)
        with self.assertRaises(GaleneUnavailable):
            self.client.create_token(
                "cards-whist-42", username="alice", permissions=["present"])

    def test_update_token_sends_etag(self):
        self.session.request.side_effect = [
            make_response(200, json_body={}, headers={"ETag": '"77-88"'}),
            make_response(204),
        ]
        self.client.update_token(
            "cards-whist-42", "tok", username="alice", permissions=["present"])

        _, kwargs = self.session.request.call_args
        self.assertEqual(kwargs["headers"]["If-Match"], '"77-88"')

    def test_delete_token_tolerates_missing_token(self):
        self.session.request.side_effect = [
            make_response(404),
        ]
        self.client.delete_token("cards-whist-42", "tok")
        self.assertEqual(self.session.request.call_count, 1)

    def test_list_groups_handles_null(self):
        self.session.request.return_value = make_response(200, json_body=None)
        self.assertEqual(self.client.list_groups(), [])

    def test_list_tokens_handles_null(self):
        self.session.request.return_value = make_response(200, json_body=None)
        self.assertEqual(self.client.list_tokens("cards-whist-42"), [])

    def test_network_error_is_wrapped(self):
        self.session.request.side_effect = requests.ConnectionError("boom")
        with self.assertRaises(GaleneUnavailable):
            self.client.get_group_etag("cards-whist-42")

    def test_server_error_is_wrapped(self):
        self.session.request.return_value = make_response(500)
        with self.assertRaises(GaleneUnavailable):
            self.client.create_group("cards-whist-42")


class GaleneServiceTests(unittest.TestCase):
    def setUp(self):
        self.client = MagicMock()
        self.client.create_token.side_effect = ["tok-alice", "tok-bob"]
        self.client.list_groups.return_value = []
        self.service = GaleneService(
            make_config(), client=self.client, expiration_hours=8,
            clock=lambda: NOW)

    def test_disabled_service_is_inert(self):
        service = GaleneService(GaleneConfig())
        self.assertFalse(service.create_room("whist", "42", 6))
        self.assertIsNone(service.join_url("whist", "42", "alice"))
        service.teardown("whist", "42", asynchronous=False)
        service.sweep({"whist": ["42"]})

    def test_create_room_registers_room(self):
        self.assertTrue(self.service.create_room("whist", "42", 6))
        self.assertTrue(self.service.video_enabled("whist", "42"))

        _, kwargs = self.client.create_group.call_args
        self.assertEqual(kwargs["max_clients"], 7)  # players + extra seats
        self.assertEqual(kwargs["expires"], NOW + timedelta(hours=8))

    def test_create_room_failure_is_not_fatal(self):
        self.client.create_group.side_effect = GaleneUnavailable("down")
        self.assertFalse(self.service.create_room("whist", "42", 6))
        self.assertFalse(self.service.video_enabled("whist", "42"))

    def test_join_url_needs_a_room(self):
        self.assertIsNone(self.service.join_url("whist", "42", "alice"))
        self.client.create_token.assert_not_called()

    def test_join_url_mints_one_token_per_player(self):
        self.service.create_room("whist", "42", 6)
        alice = self.service.join_url("whist", "42", "alice")
        bob = self.service.join_url("whist", "42", "bob")

        self.assertEqual(alice,
                         "https://galene.example.org/group/cards-whist-42/?token=tok-alice")
        self.assertEqual(bob,
                         "https://galene.example.org/group/cards-whist-42/?token=tok-bob")
        self.assertEqual(self.client.create_token.call_count, 2)
        self.assertEqual(
            self.client.create_token.call_args.kwargs["username"], "bob")

    def test_join_url_reuses_cached_token(self):
        self.service.create_room("whist", "42", 6)
        first = self.service.join_url("whist", "42", "alice")
        second = self.service.join_url("whist", "42", "alice")

        self.assertEqual(first, second)
        self.assertEqual(self.client.create_token.call_count, 1)

    def test_join_url_refreshes_near_expiry(self):
        now = [NOW]
        self.service = GaleneService(
            make_config(), client=self.client, expiration_hours=1,
            clock=lambda: now[0])
        self.client.create_token.side_effect = ["tok-1", "tok-2"]

        self.service.create_room("whist", "42", 6)
        first = self.service.join_url("whist", "42", "alice")
        self.assertEqual(self.client.create_token.call_count, 1)

        # Well before expiry the cached token is reused.
        now[0] = NOW + timedelta(minutes=20)
        self.assertEqual(self.service.join_url("whist", "42", "alice"), first)
        self.assertEqual(self.client.create_token.call_count, 1)

        # Close to expiry a new token is minted.
        now[0] = NOW + timedelta(minutes=57)
        refreshed = self.service.join_url("whist", "42", "alice")
        self.assertEqual(self.client.create_token.call_count, 2)
        self.assertIn("tok-2", refreshed)

    def test_join_url_failure_returns_none(self):
        self.service.create_room("whist", "42", 6)
        self.client.create_token.side_effect = GaleneUnavailable("down")
        self.assertIsNone(self.service.join_url("whist", "42", "alice"))

    def test_existing_group_is_replaced_on_create(self):
        self.client.create_group.side_effect = [GaleneConflict("exists"), None]
        self.client.list_tokens.return_value = ["stale"]
        self.client.get_group_etag.return_value = '"1-2"'

        self.assertTrue(self.service.create_room("whist", "42", 6))

        self.client.delete_token.assert_called_once_with(
            "cards-whist-42", "stale")
        self.client.delete_group.assert_called_once_with(
            "cards-whist-42", '"1-2"')
        self.assertEqual(self.client.create_group.call_count, 2)

    def test_page_context_for_owner_and_player(self):
        self.service.create_room("whist", "42", 6)
        owner = self.service.page_context("whist", "42", "alice", True)
        self.assertTrue(owner["video_enabled"])
        self.assertTrue(owner["video_available"])
        self.assertTrue(owner["video_owner"])
        self.assertIn("tok-alice", owner["galene_url"])

        player = self.service.page_context("whist", "42", "bob", False)
        self.assertFalse(player["video_owner"])
        self.assertIn("tok-bob", player["galene_url"])

    def test_page_context_without_room(self):
        context = self.service.page_context("whist", "42", "alice", False)
        self.assertFalse(context["video_enabled"])
        self.assertIsNone(context["galene_url"])

    def test_enable_video_creates_room_on_demand(self):
        self.assertTrue(self.service.enable_video("whist", "42", 6))
        self.assertTrue(self.service.video_enabled("whist", "42"))

    def test_disable_video_removes_room(self):
        self.service.create_room("whist", "42", 6)
        self.service.disable_video("whist", "42")
        self.assertFalse(self.service.video_enabled("whist", "42"))
        self.client.delete_group.assert_called_once()

    def test_teardown_purges_group_and_tokens(self):
        self.service.create_room("whist", "42", 6)
        self.client.list_tokens.return_value = ["tok-alice"]
        self.client.get_group_etag.return_value = '"1-2"'

        self.service.teardown("whist", "42", asynchronous=False)

        self.client.delete_token.assert_called_once_with(
            "cards-whist-42", "tok-alice")
        self.client.delete_group.assert_called_once_with(
            "cards-whist-42", '"1-2"')
        self.assertFalse(self.service.video_enabled("whist", "42"))

    def test_teardown_never_raises(self):
        self.service.create_room("whist", "42", 6)
        self.client.list_tokens.side_effect = GaleneUnavailable("down")
        self.client.get_group_etag.side_effect = GaleneUnavailable("down")
        self.service.teardown("whist", "42", asynchronous=False)

    def test_failure_pauses_further_calls(self):
        with patch("romwhist.galene.service.time.monotonic", return_value=1000.0):
            self.client.create_group.side_effect = GaleneUnavailable("down")
            self.service.create_room("whist", "42", 6)
            self.assertFalse(self.service.available())

            # While paused, Galene is not contacted again.
            self.assertFalse(self.service.create_room("whist", "43", 6))
            self.assertEqual(self.client.create_group.call_count, 1)

        later = 1000.0 + UNAVAILABLE_COOLDOWN_SECONDS + 1
        with patch("romwhist.galene.service.time.monotonic", return_value=later):
            self.assertTrue(self.service.available())

    def test_sweep_removes_orphaned_groups(self):
        self.client.list_groups.return_value = [
            "cards-whist-42",      # live
            "cards-whist-99",      # game is gone
            "famjam",              # not ours
        ]
        self.client.get_group_etag.return_value = '"1-2"'

        self.service.sweep({"whist": ["42"]})

        deleted = [c.args[0] for c in self.client.delete_group.call_args_list]
        self.assertEqual(deleted, ["cards-whist-99"])

    def test_sweep_leaves_other_game_types_alone(self):
        self.client.list_groups.return_value = [
            "cards-belote-7",      # a different game type, still running
            "cards-whist-42",      # ours, still running
        ]
        self.service.create_room("belote", "7", 4)
        self.service.create_room("whist", "42", 6)

        # A whist game creation triggers a sweep for whist only.
        self.service.sweep({"whist": ["42"]})

        self.client.delete_group.assert_not_called()
        self.assertTrue(self.service.video_enabled("belote", "7"))
        self.assertTrue(self.service.video_enabled("whist", "42"))

    def test_sweep_forgets_rooms_of_vanished_games(self):
        self.service.create_room("whist", "42", 6)
        self.client.list_groups.return_value = []
        self.service.sweep({"whist": []})
        self.assertFalse(self.service.video_enabled("whist", "42"))

    def test_sweep_skips_when_galene_down(self):
        self.client.list_groups.side_effect = GaleneUnavailable("down")
        self.service.sweep({"whist": ["42"]})
        self.client.delete_group.assert_not_called()


if __name__ == "__main__":
    unittest.main()


class GaleneRouteTests(unittest.TestCase):
    """Route level checks: the video feature must never break gameplay."""

    def setUp(self):
        # create_app() cannot be called twice in one process: reuse the module
        # level application shared by the other route tests.
        self.app = flask_app
        self.app.config["TESTING"] = True
        ensure_bootstrap(self.app)
        self.client = self.app.test_client()
        # A fresh registry per test so tests do not leak state.
        self.service = GaleneService(make_config(), client=MagicMock(),
                                     expiration_hours=8, clock=lambda: NOW)

    def _post_start(self, endpoint, extra=None, video=False):
        data = {"user_name": "alice", "start_game": "y"}
        if video:
            data["video_chat"] = "y"
        data.update(extra or {})
        return self.client.post(endpoint, data=data, follow_redirects=False)

    def test_no_room_created_without_checkbox(self):
        with patch.object(video, "get_service", return_value=self.service), \
                patch.object(ohell_routes, "games", {}), \
                patch.object(ohell_routes, "clients", {}):
            response = self._post_start("/ohell_start", {"increment": 1})

        self.service.client.create_group.assert_not_called()
        self.assertEqual(response.status_code, 302)

    def test_room_created_when_checkbox_checked(self):
        with patch.object(video, "get_service", return_value=self.service), \
                patch.object(ohell_routes, "games", {}), \
                patch.object(ohell_routes, "clients", {}):
            response = self._post_start(
                "/ohell_start", {"increment": 1}, video=True)

        self.assertEqual(response.status_code, 302)
        self.service.client.create_group.assert_called_once()
        group = self.service.client.create_group.call_args.args[0]
        self.assertTrue(group.startswith("cards-whist-"))
        self.assertTrue(self.service.video_enabled(
            "whist", group.rsplit("-", 1)[-1]))

    def test_game_still_created_when_galene_is_down(self):
        self.service.client.create_group.side_effect = GaleneUnavailable("down")
        with patch.object(video, "get_service", return_value=self.service), \
                patch.object(ohell_routes, "games", {}) as games, \
                patch.object(ohell_routes, "clients", {}):
            response = self._post_start(
                "/ohell_start", {"increment": 1}, video=True)

        # The game exists and the player was redirected to it.
        self.assertEqual(response.status_code, 302)
        self.assertEqual(len(games), 1)

    def test_start_page_renders_video_checkbox(self):
        response = self.client.get("/ohell_start")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'name="video_chat"', response.data)

    def test_video_button_absent_when_room_not_enabled(self):
        response = self.client.get("/ohell_start")
        self.assertNotIn(b"add_video_button('", response.data)

    def test_game_page_declares_video_variables_inside_script(self):
        """The include must not close the surrounding <script> block early."""
        template = flask_app.jinja_env.get_template("galene_button_vars.html")
        rendered = template.render(
            video_enabled=True, video_available=True, video_owner=False,
            galene_url="https://galene.example.org/group/g/?token=t")
        self.assertNotIn("<script", rendered)
        self.assertNotIn("</script>", rendered)
        self.assertIn("var video_enabled = true;", rendered)
        self.assertIn('var galene_url = "https://galene.example.org/group/g/?token=t";',
                      rendered)

    def test_every_game_template_includes_video_variables(self):
        import os
        import pathlib
        folder = pathlib.Path(
            os.path.join(flask_app.root_path, flask_app.template_folder))
        games = {"ohell.html", "belote.html", "contree.html", "poker.html"}
        for name in games:
            text = (folder / name).read_text()
            self.assertIn("galene_button_vars.html", text, name)
            self.assertIn("add_video_button(", text, name)


if __name__ == "__main__":
    unittest.main()
